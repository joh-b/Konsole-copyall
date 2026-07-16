#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import re
import sys


EXPECTED_PATHS = {"src/main.cpp"}
PATCH_LICENSE = "SPDX-License-Identifier: GPL-2.0-or-later"

REQUIRED_ADDITIONS = (
    'i18nc("@title", "Konsole Custom"),',
    'about.setDesktopFileName(QStringLiteral("org.kde.konsole-custom"));',
    "const QString upstreamApplicationName = QCoreApplication::applicationName();",
    'QCoreApplication::setApplicationName(QStringLiteral("konsole-custom"));',
    "QCoreApplication::setApplicationName(upstreamApplicationName);",
)

REQUIRED_REMOVALS = (
    'i18nc("@title", "Konsole"),',
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify-identity-patch.py PATCH")

    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    preamble = text.split("\ndiff --git ", maxsplit=1)[0]
    if PATCH_LICENSE not in preamble:
        fail(f"patch preamble is missing {PATCH_LICENSE}")

    path_pairs = re.findall(r"^diff --git a/(\S+) b/(\S+)$", text, re.MULTILINE)
    if any(left != right for left, right in path_pairs):
        fail("an identity patch entry renames a file")

    paths = {left for left, _ in path_pairs}
    if paths != EXPECTED_PATHS:
        fail(f"patched paths are {sorted(paths)!r}, expected {sorted(EXPECTED_PATHS)!r}")

    added_lines = [
        line[1:]
        for line in text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    removed_lines = [
        line[1:]
        for line in text.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]
    additions = "\n".join(added_lines)
    removals = "\n".join(removed_lines)

    for required in REQUIRED_ADDITIONS:
        if required not in additions:
            fail(f"required addition is missing: {required}")

    for required in REQUIRED_REMOVALS:
        if required not in removals:
            fail(f"required removal is missing: {required}")

    if 'KLocalizedString::setApplicationDomain("konsole-custom")' in text:
        fail("the translation domain must remain the upstream 'konsole' domain")
    if '-    KLocalizedString::setApplicationDomain("konsole");' in text:
        fail("the identity patch removes the upstream translation domain")
    if '-    KAboutData about(QStringLiteral("konsole"),' in text:
        fail("the permanent application name must remain 'konsole' for full-app behavior")
    if '+    KAboutData about(QStringLiteral("konsole-custom"),' in text:
        fail("the permanent application name must not make Konsole behave as a KPart")

    isolated_registration = re.compile(
        r'QCoreApplication::setApplicationName\(QStringLiteral\("konsole-custom"\)\);.*'
        r"KDBusService dbusService\(startupOption \| KDBusService::NoExitOnFailure\);.*"
        r"QCoreApplication::setApplicationName\(upstreamApplicationName\);",
        re.DOTALL,
    )
    if not isolated_registration.search(text):
        fail("the custom D-Bus name is not set and restored around registration")

    print("Konsole custom identity patch structure is valid")


if __name__ == "__main__":
    main()
