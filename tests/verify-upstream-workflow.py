#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import sys


ORDERED_GATES = (
    "Require Cachix publication settings",
    "nix store prefetch-file --json",
    "nix flake update nixpkgs",
    "nix flake check --print-build-logs",
    "nix build .#default --print-build-logs",
    'cachix push "$CACHE_NAME" "$store_path"',
    "git commit -m",
    "git push origin HEAD:main",
)

REQUIRED_CONTENT = (
    'cron: "37 3 * * *"',
    "contents: write",
    "repos/KDE/konsole/tags?per_page=100",
    "scripts/select_latest_stable_tag.py",
    "CACHIX_CACHE_NAME",
    "CACHIX_AUTH_TOKEN",
    "nix/upstream.json",
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify-upstream-workflow.py WORKFLOW")

    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    for required in REQUIRED_CONTENT:
        if required not in text:
            fail(f"upstream workflow is missing: {required}")

    positions = []
    for gate in ORDERED_GATES:
        position = text.find(gate)
        if position < 0:
            fail(f"upstream workflow is missing gate: {gate}")
        positions.append(position)

    if positions != sorted(positions):
        fail("upstream workflow can commit before all build/publication gates pass")

    print("Upstream workflow has ordered detection, build, publication, and commit gates")


if __name__ == "__main__":
    main()
