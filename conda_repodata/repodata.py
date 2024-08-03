# Copyright (C) 2023 Ken Odegard
# SPDX-License-Identifier: BSD-3-Clause
"""Conda repodata subcommand and repodata patching."""
import json
import os.path
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Iterable, Sized

import click
from conda.base.constants import REPODATA_FN
from conda.base.context import context
from conda.common.constants import NULL
from conda.core.index import check_allowlist
from conda.exceptions import CondaError
from conda.gateways.repodata import (
    CondaRepoInterface,
    RepodataFetch,
    cache_fn_url,
    create_cache_dir,
)
from conda.models.channel import Channel, all_channel_urls
from conda.plugins import CondaRepodataPatch, CondaSubcommand, hookimpl
from rich import print
from rich.pretty import Pretty
from rich.table import Table

from . import __version__

SUBCOMMAND = "repodata"
PROG_NAME = f"conda {SUBCOMMAND}"
REPODATA_KEYS = {"info", "packages", "packages.conda", "removed", "repodata_version"}


@click.command()
@click.version_option(__version__)
@click.help_option("--help", "-h")
@click.option("--channels", "--channel", "-c", multiple=True)
@click.option("--subdirs", "--subdir", "--platforms", "--platform", multiple=True)
@click.option(
    "--stats",
    is_flag=True,
    default=False,
    help="Show the stats between the original and patched repodata.",
)
@click.option("--output", help="Save repodata.json to provided path.", type=Path)
@click.option("--force", is_flag=True, default=False, help="Overwrite existing file.")
def cli(
    channels: Iterable[str],
    subdirs: Iterable[str],
    stats: bool,
    output: Path,
    force: bool,
):
    """Manipulate or inspect the repodata.json locally."""
    context.__init__(
        argparse_args={"channels": channels or NULL, "subdirs": subdirs or NULL}
    )

    channel_urls = all_channel_urls(context.channels)
    check_allowlist(channel_urls)

    repodatas = []
    for channel in map(Channel, channel_urls):
        repodata_fetch = RepodataFetch(
            cache_path_base=Path(
                create_cache_dir(),
                cache_fn_url(channel.url(with_credentials=True), REPODATA_FN),
            ).with_suffix(""),
            channel=channel,
            repodata_fn=REPODATA_FN,
            repo_interface_cls=CondaRepoInterface,
        )

        original, _ = repodata_fetch.fetch_latest()
        if isinstance(original, str):
            original = json.loads(original)
        patched, _ = repodata_fetch.fetch_latest_parsed()

        repodatas.append((channel, original, patched))

    if stats:
        for channel, original, patched in repodatas:
            table = Table(title=str(channel))
            table.add_column("field")
            table.add_column("original")
            table.add_column("patched")

            for key in sorted({*original, *patched}):
                table.add_row(
                    key, _pretty(original.get(key)), _pretty(patched.get(key))
                )

            print(table)
    elif output:
        if output.is_file() and not force:
            raise CondaError(f"Output file already exists ({output}).")
        elif output.is_dir() or len(repodatas) > 1:
            for channel, _, patched in repodatas:
                path = output / channel.name / channel.subdir / REPODATA_FN
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_file() and not force:
                    raise CondaError(f"Output file already exists ({path}).")
                path.write_text(json.dumps(patched, indent=2))
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(repodatas[0][-1], indent=2))

    elif len(repodatas) > 1:
        raise CondaError(
            "Too many channels/subdirs specified to dump to stdout. "
            "Be more selective with your channel/subdir selection."
        )
    else:
        print(json.dumps(repodatas[0][-1], indent=2))


def _pretty(value: Any, cutoff: int = 5):
    if value is None:
        return ""

    if isinstance(value, str):
        # display strings as is
        return value

    # display small iterables, count large ones
    if isinstance(value, Sized) and len(value) > cutoff:
        return Pretty(len(value))
    return Pretty(value)


def apply_transformations(channel: Channel, repodata: dict) -> dict:
    """Apply repodata transformations."""
    for transformation in filter(
        None,
        os.environ.get("CONDA_TRANSFORMATIONS", "").split(","),
    ):
        try:
            if Path(transformation).is_file():
                # full path to a script, the script must define a function called transformer
                spec = spec_from_file_location("transformation", transformation)
                if not spec or not spec.loader:
                    raise ImportError(transformation)
                module = module_from_spec(spec)
                # sys.modules["transformation"] = module
                spec.loader.exec_module(module)
                function_name = "transformation"
            else:
                # support a full import path and entrypoint syntax:
                # pkg.module.function
                # pkg.module:function
                import_path, function_name = transformation.rsplit(
                    ":" if ":" in transformation else ".", 1
                )

                module = import_module(import_path)
        except Exception as err:
            raise CondaError(
                f"Failed to import transformation ({transformation})\nreason: {err!r}"
            )

        function = getattr(module, function_name)

        try:
            repodata = function(channel, repodata)
        except BaseException as err:
            raise CondaError(
                f"Failed to apply transformation ({transformation})\nreason: {err!r}"
            )

    return repodata


@hookimpl
def conda_repodata_patches():
    """Register repodata patches."""
    yield CondaRepodataPatch(
        name="apply_transformations",
        action=apply_transformations,
    )


@hookimpl
def conda_subcommands():
    """Register repodata subcommand."""
    yield CondaSubcommand(
        name=SUBCOMMAND,
        action=lambda argv: cli(argv, prog_name=PROG_NAME),
        summary=cli.__doc__,
    )
