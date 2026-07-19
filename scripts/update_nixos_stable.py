#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
from pathlib import Path
import re


STABLE_VERSION = re.compile(r"^\d{2}\.(?:05|11)$")
FLAKE_REF = re.compile(
    r"github:NixOS/nixpkgs/nixos-(?P<version>\d{2}\.(?:05|11))"
)
WORKFLOW_DEFAULT = re.compile(
    r"(?m)^(\s*default: nixos-)(?P<version>\d{2}\.(?:05|11))$"
)


def read_once(path: Path, pattern: re.Pattern[str]) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one stable reference in {path}, found {len(matches)}")
    return text, matches[0].group("version")


def replace_once(path: Path, text: str, pattern: re.Pattern[str], replacement: str) -> None:
    updated, count = pattern.subn(replacement, text)
    if count != 1:
        raise AssertionError(f"failed to update exactly one reference in {path}")
    path.write_text(updated, encoding="utf-8")


def update(root: Path, target: str) -> str:
    if STABLE_VERSION.fullmatch(target) is None:
        raise ValueError(f"not a stable NixOS release: {target}")

    flake = root / "flake.nix"
    workflow = root / ".github/workflows/compatibility.yml"
    flake_text, current_flake = read_once(flake, FLAKE_REF)
    workflow_text, current_workflow = read_once(workflow, WORKFLOW_DEFAULT)

    if current_flake != current_workflow:
        raise ValueError(
            "flake.nix and compatibility.yml selected different stable releases "
            f"({current_flake} and {current_workflow})"
        )
    if tuple(map(int, target.split("."))) <= tuple(map(int, current_flake.split("."))):
        raise ValueError(f"refusing non-forward transition from {current_flake} to {target}")

    replace_once(
        flake,
        flake_text,
        FLAKE_REF,
        f"github:NixOS/nixpkgs/nixos-{target}",
    )
    replace_once(
        workflow,
        workflow_text,
        WORKFLOW_DEFAULT,
        rf"\g<1>{target}",
    )
    return current_flake


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    previous = update(args.root, args.version)
    print(f"Updated NixOS stable {previous} -> {args.version}")


if __name__ == "__main__":
    main()
