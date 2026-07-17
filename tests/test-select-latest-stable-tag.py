#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import unittest


SCRIPT = Path(
    os.environ.get(
        "SELECTOR_SCRIPT",
        Path(__file__).parents[1] / "scripts" / "select_latest_stable_tag.py",
    )
)
SPEC = spec_from_file_location("select_latest_stable_tag", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SelectLatestStableTagTests(unittest.TestCase):
    def test_selects_highest_newer_stable_tag(self) -> None:
        tags = ["v26.04.4", "v26.08.0", "v26.04.5", "v25.12.9"]
        self.assertEqual(MODULE.newest_stable_tag(tags, "26.04.3"), "v26.08.0")

    def test_ignores_beta_rc_and_malformed_tags(self) -> None:
        tags = [
            "v26.08.80",
            "v26.08.90",
            "26.08.0",
            "v26.13.0",
            "vnext",
            "v26.04.4",
        ]
        self.assertEqual(MODULE.newest_stable_tag(tags, "v26.04.3"), "v26.04.4")

    def test_rejects_noncanonical_patch_components(self) -> None:
        self.assertIsNone(MODULE.parse_stable_tag("v26.04.04"))
        self.assertIsNone(MODULE.parse_stable_tag("v26.04.00"))

    def test_returns_none_when_current_is_latest(self) -> None:
        tags = ["v26.04.3", "v26.04.2", "v25.12.3"]
        self.assertIsNone(MODULE.newest_stable_tag(tags, "26.04.3"))

    def test_rejects_an_invalid_current_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "not a stable KDE tag"):
            MODULE.newest_stable_tag(["v26.04.3"], "rolling")


if __name__ == "__main__":
    unittest.main()
