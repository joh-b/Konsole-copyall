#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts/select_latest_nixos_stable.py"
SPEC = importlib.util.spec_from_file_location("select_latest_nixos_stable", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SelectLatestNixosStableTests(unittest.TestCase):
    def test_selects_only_a_newer_final_release(self) -> None:
        tags = ["26.05", "26.11-pre", "26.11-beta", "25.11", "nixos-26.11"]
        self.assertIsNone(MODULE.select_latest(tags, "26.05"))

        tags.append("26.11")
        self.assertEqual(MODULE.select_latest(tags, "26.05"), "26.11")

    def test_selects_the_highest_release_independent_of_input_order(self) -> None:
        tags = ["27.05", "26.11", "27.05", "25.11"]
        self.assertEqual(MODULE.select_latest(tags, "26.05"), "27.05")

    def test_rejects_an_invalid_current_release(self) -> None:
        with self.assertRaisesRegex(ValueError, "not a stable NixOS release"):
            MODULE.select_latest(["26.11"], "unstable")


if __name__ == "__main__":
    unittest.main()
