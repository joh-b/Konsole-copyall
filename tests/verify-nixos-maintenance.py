#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import re
import sys


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require_text(path: Path, values: tuple[str, ...], subject: str) -> str:
    text = path.read_text(encoding="utf-8")
    for value in values:
        if value not in text:
            fail(f"{subject} is missing: {value}")
    return text


def verify_dependabot(path: Path) -> None:
    text = require_text(
        path,
        (
            'package-ecosystem: "nix"',
            'directory: "/"',
            'interval: "weekly"',
            'day: "monday"',
            'time: "04:00"',
            'timezone: "Europe/Zurich"',
            'exclude:',
            '- "*"',
            'open-pull-requests-limit: 1',
        ),
        "Dependabot configuration",
    )
    if text.count('package-ecosystem: "nix"') != 1:
        fail("Dependabot must contain exactly one Nix update configuration")


def verify_dependabot_merge(path: Path) -> None:
    require_text(
        path,
        (
            "workflow_run:",
            "github.event.workflow_run.conclusion == 'success'",
            "github.event.workflow_run.event == 'pull_request'",
            "GH_REPO: ${{ github.repository }}",
            "dependabot[bot]",
            "dependabot/nix/*",
            "'[\"flake.lock\"]'",
            "compare/main...$HEAD_SHA",
            "refusing a stale merge",
            ".nodes.nixpkgs.original.ref",
            ".nodes.nixpkgs.locked.owner",
            "changed the identity of the locked nixpkgs input",
            '--match-head-commit "$HEAD_SHA"',
            "gh workflow run publish.yml --ref main",
        ),
        "Dependabot merge workflow",
    )


def verify_workflow(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required = (
        "actions: write",
        "contents: write",
        "pull-requests: write",
        "repos/NixOS/nixpkgs/tags?per_page=100",
        "scripts/select_latest_nixos_stable.py",
        "scripts/update_nixos_stable.py",
        "nix flake update nixpkgs",
        "git push",
        "gh pr create",
        "gh pr reopen",
        "gh workflow run check.yml",
        "gh run watch",
        'echo "base_sha=$(git rev-parse HEAD^)"',
        "Main moved after the stable transition was tested",
        "gh pr merge",
        "gh workflow run publish.yml --ref main",
        '--commit "$main_sha"',
        "The dispatched publish workflow run was not found",
    )
    for value in required:
        if value not in text:
            fail(f"stable-release workflow is missing: {value}")

    ordered = (
        "repos/NixOS/nixpkgs/tags?per_page=100",
        "scripts/select_latest_nixos_stable.py",
        "scripts/update_nixos_stable.py",
        "nix flake update nixpkgs",
        "git push",
        "gh pr create",
        "gh workflow run check.yml",
        "gh run watch",
        "gh pr merge",
        "Ensure the current main revision is published",
        "gh workflow run publish.yml --ref main",
    )
    positions = [text.find(value) for value in ordered]
    if positions != sorted(positions):
        fail("stable-release workflow gates are out of order")


def selected_version(path: Path, pattern: str) -> str:
    matches = re.findall(pattern, path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    if len(matches) != 1:
        fail(f"expected exactly one selected stable release in {path}")
    return matches[0]


def main() -> None:
    if len(sys.argv) != 6:
        fail(
            "usage: verify-nixos-maintenance.py DEPENDABOT DEPENDABOT_MERGE "
            "STABLE_WORKFLOW FLAKE COMPATIBILITY"
        )

    dependabot, dependabot_merge, stable_workflow, flake, compatibility = map(
        Path, sys.argv[1:]
    )
    verify_dependabot(dependabot)
    verify_dependabot_merge(dependabot_merge)
    verify_workflow(stable_workflow)

    flake_version = selected_version(
        flake,
        r"github:NixOS/nixpkgs/nixos-(\d{2}\.(?:05|11))",
    )
    workflow_version = selected_version(
        compatibility,
        r"^\s*default: nixos-(\d{2}\.(?:05|11))$",
    )
    if flake_version != workflow_version:
        fail("flake and compatibility workflow select different stable releases")

    print(
        f"NixOS {flake_version} uses gated stable promotion and verified weekly lock maintenance"
    )


if __name__ == "__main__":
    main()
