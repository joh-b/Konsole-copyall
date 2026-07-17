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
    "skipPush: true",
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require_pull_only_cache(text: str, next_step: str, workflow_name: str) -> None:
    configure_position = text.find("- name: Configure Cachix")
    next_position = text.find(next_step)
    if configure_position < 0 or next_position < 0 or next_position <= configure_position:
        fail(f"{workflow_name} has a malformed Cachix configuration block")

    configure_block = text[configure_position:next_position]
    if "skipPush: true" not in configure_block:
        fail(f"{workflow_name} Cachix setup must remain pull-only until verification passes")


def verify_release_workflow(text: str) -> None:
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

    require_pull_only_cache(text, "- name: Check the new upstream release", "upstream workflow")

    if text.count('cachix push "$CACHE_NAME" "$store_path"') != 1:
        fail("upstream workflow must have exactly one explicit publication command")


def verify_publish_workflow(text: str) -> None:
    require_pull_only_cache(text, "- name: Check and build", "publish workflow")

    gates = (
        "nix flake check --print-build-logs",
        "nix build .#default --print-build-logs",
        'cachix push "$CACHE_NAME" "$(readlink -f result)"',
    )
    positions = [text.find(gate) for gate in gates]
    if any(position < 0 for position in positions):
        fail("publish workflow is missing a verification or publication gate")
    if positions != sorted(positions):
        fail("publish workflow can publish before all checks and builds pass")
    if text.count('cachix push "$CACHE_NAME"') != 1:
        fail("publish workflow must have exactly one explicit publication command")


def main() -> None:
    if len(sys.argv) != 3:
        fail("usage: verify-upstream-workflow.py UPSTREAM_WORKFLOW PUBLISH_WORKFLOW")

    release_text = Path(sys.argv[1]).read_text(encoding="utf-8")
    publish_text = Path(sys.argv[2]).read_text(encoding="utf-8")
    verify_release_workflow(release_text)
    verify_publish_workflow(publish_text)

    print("Cachix remains pull-only until ordered verification and publication gates pass")


if __name__ == "__main__":
    main()
