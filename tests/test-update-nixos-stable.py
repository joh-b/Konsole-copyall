#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts/update_nixos_stable.py"
SPEC = importlib.util.spec_from_file_location("update_nixos_stable", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class UpdateNixosStableTests(unittest.TestCase):
    def make_root(self, flake_version: str = "26.05", workflow_version: str = "26.05") -> Path:
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (root / ".github/workflows").mkdir(parents=True)
        (root / "flake.nix").write_text(
            f'inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-{flake_version}";\n',
            encoding="utf-8",
        )
        (root / ".github/workflows/compatibility.yml").write_text(
            f"inputs:\n  nixpkgs_ref:\n    default: nixos-{workflow_version}\n",
            encoding="utf-8",
        )
        return root

    def test_updates_both_versioned_references(self) -> None:
        root = self.make_root()
        self.assertEqual(MODULE.update(root, "26.11"), "26.05")
        self.assertIn("nixos-26.11", (root / "flake.nix").read_text(encoding="utf-8"))
        self.assertIn(
            "default: nixos-26.11",
            (root / ".github/workflows/compatibility.yml").read_text(encoding="utf-8"),
        )

    def test_rejects_disagreeing_references(self) -> None:
        root = self.make_root(workflow_version="25.11")
        with self.assertRaisesRegex(ValueError, "selected different stable releases"):
            MODULE.update(root, "26.11")

    def test_rejects_non_forward_and_non_final_releases(self) -> None:
        root = self.make_root()
        with self.assertRaisesRegex(ValueError, "refusing non-forward transition"):
            MODULE.update(root, "25.11")
        with self.assertRaisesRegex(ValueError, "not a stable NixOS release"):
            MODULE.update(self.make_root(), "26.11-beta")


if __name__ == "__main__":
    unittest.main()
