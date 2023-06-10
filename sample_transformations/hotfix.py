# Copyright (C) 2023 Ken Odegard
# SPDX-License-Identifier: BSD-3-Clause
"""A sample repodata hotfix implementation."""


def transformation(repodata: dict) -> dict:
    """Iterate over repodata packages and apply patch_patch function."""
    for key in ["packages", "packages.conda"]:
        for package, meta in repodata[key].items():
            package_patch(package, meta)
    return repodata


def package_patch(package: str, meta: dict) -> dict:
    """Perform inplace patching of a package's metadata."""
    if meta["name"] == "zlib" and meta["version"] == "1.2.13":
        meta["depends"].append("python")
