# Copyright (C) 2023 Ken Odegard
# SPDX-License-Identifier: BSD-3-Clause
"""Implements conda repodata subcommand and POC repodata patching."""
import difflib
import json
from pathlib import Path
from typing import Iterable

import click
from conda.base.constants import REPODATA_FN
from conda.gateways.repodata import (
    CondaRepoInterface,
    RepodataFetch,
    cache_fn_url,
    create_cache_dir,
)
from conda.models.channel import Channel
from conda.plugins import CondaRepodataPatch, CondaSubcommand, hookimpl
from rich import print
from rich.table import Table


@click.command()
@click.option("--channels", "--channel", "-c", multiple=True, type=Channel)
@click.option(
    "--diff",
    is_flag=True,
    default=False,
    help="Show the diff between the original and patched repodata.",
)
def cli(channels: Iterable[Channel], diff: bool):
    """Manipulate or inspect the repodata.json locally."""
    repodatas = {}
    for channel in channels:
        repodata_fetch = RepodataFetch(
            cache_path_base=Path(
                create_cache_dir(),
                cache_fn_url(channel.url(with_credentials=True) or "", REPODATA_FN),
            ).with_suffix(""),
            channel=channel,
            repodata_fn=REPODATA_FN,
            repo_interface_cls=CondaRepoInterface,
        )
        repodatas[channel] = {
            "original": json.dumps(repodata_fetch._fetch_latest()),
            "patched": json.dumps(repodata_fetch.fetch_latest()),
        }

    if diff:
        grid = Table.grid(expand=True)
        grid.add_column()
        for channel, jsons in repodatas.items():
            grid.add_row(Channel)
            grid.add_row(difflib.unified_diff(jsons["original"], jsons["patched"]))
        print(grid)


def poc_repodata_patch(repodata: dict) -> dict:
    """POC repodata patch."""
    repodata["conda_repodata_patch"] = "Hello from conda_repodata_patch"
    return repodata


@hookimpl
def conda_repodata_patches():
    """Register repodata patches."""
    yield CondaRepodataPatch(
        name="poc_repodata_patch",
        action=poc_repodata_patch,
    )


@hookimpl
def conda_subcommand():
    """Register repodata subcommand."""
    yield CondaSubcommand(
        name="repodata",
        action=cli,
        summary=cli.__doc__,
    )
