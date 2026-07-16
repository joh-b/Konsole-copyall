#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import json
from pathlib import Path
import re
import sys


VERSION = re.compile(r"^\d{2}\.\d{2}\.\d+$")
SRI_HASH = re.compile(r"^sha256-[A-Za-z0-9+/]{43}=$")


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify-upstream-metadata.py UPSTREAM_JSON")

    metadata = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if set(metadata) != {"version", "tag", "url", "hash"}:
        fail(f"unexpected metadata keys: {sorted(metadata)}")

    version = metadata["version"]
    if not isinstance(version, str) or VERSION.fullmatch(version) is None:
        fail(f"invalid stable version: {version!r}")
    _, cycle, patch = (int(part) for part in version.split("."))
    if not 1 <= cycle <= 12 or patch >= 50:
        fail(f"version is a KDE prerelease or has an invalid cycle: {version!r}")
    if metadata["tag"] != f"v{version}":
        fail("tag does not match the pinned version")

    expected_url = (
        f"https://download.kde.org/stable/release-service/{version}/src/"
        f"konsole-{version}.tar.xz"
    )
    if metadata["url"] != expected_url:
        fail("source URL does not match the pinned version")
    if not isinstance(metadata["hash"], str) or SRI_HASH.fullmatch(metadata["hash"]) is None:
        fail("source hash is not a canonical sha256 SRI hash")

    print(f"Upstream metadata consistently pins Konsole {version}")


if __name__ == "__main__":
    main()
