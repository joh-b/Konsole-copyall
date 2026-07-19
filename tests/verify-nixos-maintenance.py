#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import json
from pathlib import Path
import re
import sys


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def verify_renovate(path: Path) -> None:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("enabledManagers") != ["nix"] or config.get("nix") != {"enabled": True}:
        fail("Renovate must enable only its Nix manager")

    maintenance = config.get("lockFileMaintenance", {})
    required = {
        "enabled": True,
        "schedule": ["before 5am on monday"],
        "automerge": True,
        "automergeType": "pr",
        "platformAutomerge": False,
    }
    if any(maintenance.get(key) != value for key, value in required.items()):
        fail("weekly lock maintenance is not configured for verified Renovate merge")

    rules = config.get("packageRules", [])
    if not any(
        rule.get("matchPackageNames") == ["https://github.com/NixOS/nixpkgs"]
        and rule.get("enabled") is False
        for rule in rules
    ):
        fail("ordinary Renovate nixpkgs branch updates must remain disabled")
    if not any(
        rule.get("matchUpdateTypes") == ["lockFileMaintenance"]
        and rule.get("enabled") is True
        and rule.get("automerge") is True
        and rule.get("platformAutomerge") is False
        for rule in rules
    ):
        fail("Renovate lock maintenance must be explicitly enabled and automerged")


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
        "gh workflow run check.yml",
        "gh run watch",
        "gh pr merge",
        "gh workflow run publish.yml --ref main",
    )
    for value in required:
        if value not in text:
            fail(f"stable-release workflow is missing: {value}")

    positions = [text.find(value) for value in required[3:]]
    if positions != sorted(positions):
        fail("stable-release workflow gates are out of order")


def selected_version(path: Path, pattern: str) -> str:
    matches = re.findall(pattern, path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    if len(matches) != 1:
        fail(f"expected exactly one selected stable release in {path}")
    return matches[0]


def main() -> None:
    if len(sys.argv) != 5:
        fail("usage: verify-nixos-maintenance.py RENOVATE STABLE_WORKFLOW FLAKE COMPATIBILITY")

    renovate, stable_workflow, flake, compatibility = map(Path, sys.argv[1:])
    verify_renovate(renovate)
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

    print(f"NixOS {flake_version} uses gated stable promotion and weekly lock maintenance")


if __name__ == "__main__":
    main()
