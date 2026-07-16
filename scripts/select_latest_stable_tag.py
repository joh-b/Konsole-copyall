#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import re
import sys
from collections.abc import Iterable


STABLE_TAG = re.compile(r"^v(?P<year>\d{2})\.(?P<cycle>\d{2})\.(?P<patch>\d+)$")
FIRST_PRERELEASE_PATCH = 50


def parse_stable_tag(tag: str) -> tuple[int, int, int] | None:
    match = STABLE_TAG.fullmatch(tag.strip())
    if match is None:
        return None

    version = tuple(int(match.group(part)) for part in ("year", "cycle", "patch"))
    _, cycle, patch = version
    if not 1 <= cycle <= 12 or patch >= FIRST_PRERELEASE_PATCH:
        return None
    return version


def newest_stable_tag(tags: Iterable[str], current: str) -> str | None:
    normalized_current = current if current.startswith("v") else f"v{current}"
    current_version = parse_stable_tag(normalized_current)
    if current_version is None:
        raise ValueError(f"current version is not a stable KDE tag: {current!r}")

    candidates = {
        version: tag.strip()
        for tag in tags
        if (version := parse_stable_tag(tag)) is not None and version > current_version
    }
    if not candidates:
        return None
    return candidates[max(candidates)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select the newest stable KDE Konsole tag newer than the current version."
    )
    parser.add_argument("--current", required=True, help="current version or v-prefixed tag")
    args = parser.parse_args()

    try:
        selected = newest_stable_tag(sys.stdin, args.current)
    except ValueError as error:
        parser.error(str(error))

    if selected is not None:
        print(selected)


if __name__ == "__main__":
    main()
