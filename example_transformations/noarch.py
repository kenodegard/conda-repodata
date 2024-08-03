# Copyright (C) 2023 Ken Odegard
# SPDX-License-Identifier: BSD-3-Clause
"""A sample transformation that drops non-noarch packages."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conda.models.channel import Channel


def transformation(channel: Channel, repodata: dict) -> dict:
    """Drop non-noarch packages."""
    if repodata["info"]["subdir"] == "noarch":
        return repodata
    repodata["packages"].clear()
    repodata["packages.conda"].clear()
    repodata["removed"].clear()
    return repodata
