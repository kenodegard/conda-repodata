# Copyright (C) 2023 Ken Odegard
# SPDX-License-Identifier: BSD-3-Clause
"""A sample transformation that only keeps python packages."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conda.models.channel import Channel


def transformation(channel: Channel, repodata: dict) -> dict:
    """Only keep python packages."""
    for key in ["packages", "packages.conda"]:
        repodata[key] = {
            package: meta
            for package, meta in repodata[key].items()
            if meta["name"] == "python"
        }
    return repodata
