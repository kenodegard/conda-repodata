# Copyright (C) 2023 Ken Odegard
# SPDX-License-Identifier: BSD-3-Clause
"""A sample transformation that drops OpenSSL 3.0.8 packages."""


def transformation(repodata: dict) -> dict:
    """Drop OpenSSL 3.0.8."""
    for key in ["packages", "packages.conda"]:
        repodata[key] = {
            package: meta
            for package, meta in repodata[key].items()
            if meta["name"] != "openssl" or meta["version"] != "3.0.8"
        }
    return repodata
