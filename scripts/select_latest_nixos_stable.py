#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import re
import sys


STABLE_VERSION = re.compile(r"^(?P<year>\d{2})\.(?P<month>05|11)$")


def version_key(version: str) -> tuple[int, int]:
    match = STABLE_VERSION.fullmatch(version)
    if match is None:
        raise ValueError(f"not a stable NixOS release: {version}")
    return int(match["year"]), int(match["month"])


def select_latest(tags: list[str], current: str) -> str | None:
    current_key = version_key(current)
    stable = {tag for tag in tags if STABLE_VERSION.fullmatch(tag)}
    newer = [tag for tag in stable if version_key(tag) > current_key]
    return max(newer, key=version_key, default=None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True)
    args = parser.parse_args()

    tags = [line.strip() for line in sys.stdin if line.strip()]
    latest = select_latest(tags, args.current)
    if latest is not None:
        print(latest)


if __name__ == "__main__":
    main()
