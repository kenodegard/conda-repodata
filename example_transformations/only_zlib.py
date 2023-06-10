# Copyright (C) 2023 Ken Odegard
# SPDX-License-Identifier: BSD-3-Clause
"""A sample transformation that only keeps zlib packages."""


def transformation(repodata: dict) -> dict:
    """Only keep zlib packages."""
    for key in ["packages", "packages.conda"]:
        repodata[key] = {
            package: meta
            for package, meta in repodata[key].items()
            if meta["name"] == "zlib"
        }
    return repodata
