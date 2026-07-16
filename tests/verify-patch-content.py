#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import re
import sys


EXPECTED_PATHS = {
    "src/session/SessionController.cpp",
    "src/terminalDisplay/TerminalDisplay.cpp",
    "src/terminalDisplay/TerminalDisplay.h",
}

REQUIRED_ADDITIONS = (
    'QStringLiteral("copy-entire-scrollback")',
    'i18n("Copy Entire Scrollback")',
    "&TerminalDisplay::copyAllToClipboard",
    "void TerminalDisplay::copyAllToClipboard()",
    "void copyAllToClipboard();",
    "setSelectionByLineRange(0, _screenWindow->lineCount())",
    "copyToClipboard();",
)

FORBIDDEN_ADDITIONS = (
    "libei",
    "ydotool",
    "F20",
    "F21",
    "QTimer",
    "sleep",
    "D-Bus",
    "DBus",
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify-patch-content.py PATCH")

    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    path_pairs = re.findall(r"^diff --git a/(\S+) b/(\S+)$", text, re.MULTILINE)

    if any(left != right for left, right in path_pairs):
        fail("a patch entry renames a file")

    paths = {left for left, _ in path_pairs}
    if paths != EXPECTED_PATHS:
        fail(f"patched paths are {sorted(paths)!r}, expected {sorted(EXPECTED_PATHS)!r}")

    added_lines = [
        line[1:]
        for line in text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    additions = "\n".join(added_lines)

    for required in REQUIRED_ADDITIONS:
        if required not in additions:
            fail(f"required addition is missing: {required}")

    for forbidden in FORBIDDEN_ADDITIONS:
        if forbidden.casefold() in additions.casefold():
            fail(f"forbidden addition is present: {forbidden}")

    action_registration = re.compile(
        r'addAction\(QStringLiteral\("copy-entire-scrollback"\),\s*'
        r"view\(\)\.data\(\),\s*&TerminalDisplay::copyAllToClipboard\)"
    )
    if not action_registration.search(additions):
        fail("the action is not connected directly to the active TerminalDisplay")

    print("Konsole copy-all patch structure is valid")


if __name__ == "__main__":
    main()
