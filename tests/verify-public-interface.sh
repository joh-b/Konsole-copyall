#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later

set -euo pipefail

if (( $# != 2 )); then
    printf 'usage: %s KONSOLE_CUSTOM_STORE_PATH PATCHED_KONSOLE_STORE_PATH\n' "$0" >&2
    exit 2
fi

result=$1
patched_result=$2
executable="$result/bin/konsole-custom"
desktop="$result/share/applications/org.kde.konsole-custom.desktop"
wrapped_executable="$patched_result/bin/konsole"

if [[ ! -x "$executable" ]]; then
    printf 'custom executable not found in %s\n' "$result" >&2
    exit 1
fi

if [[ -e "$result/bin/konsole" ]]; then
    printf 'public package unexpectedly shadows bin/konsole\n' >&2
    exit 1
fi

if ! grep --fixed-strings -- "$wrapped_executable" "$executable" >/dev/null; then
    printf 'custom executable does not wrap the patched Konsole executable\n' >&2
    exit 1
fi

if [[ ! -f "$desktop" ]]; then
    printf 'custom desktop entry not found in %s\n' "$result" >&2
    exit 1
fi

if [[ -e "$result/share/applications/org.kde.konsole.desktop" ]]; then
    printf 'public package unexpectedly exposes the upstream desktop entry\n' >&2
    exit 1
fi

mapfile -t public_executables < <(find "$result/bin" -mindepth 1 -maxdepth 1 -printf '%f\n' | sort)
if (( ${#public_executables[@]} != 1 )) || [[ "${public_executables[0]}" != konsole-custom ]]; then
    printf 'unexpected public executables: %s\n' "${public_executables[*]}" >&2
    exit 1
fi

mapfile -t public_desktops < <(find "$result/share/applications" -mindepth 1 -maxdepth 1 -printf '%f\n' | sort)
if (( ${#public_desktops[@]} != 1 )) || [[ "${public_desktops[0]}" != org.kde.konsole-custom.desktop ]]; then
    printf 'unexpected public desktop entries: %s\n' "${public_desktops[*]}" >&2
    exit 1
fi

desktop-file-validate "$desktop"

for expected in \
    "TryExec=$executable" \
    "Exec=$executable" \
    "Exec=$executable --new-tab"
do
    if ! grep --fixed-strings --line-regexp -- "$expected" "$desktop" >/dev/null; then
        printf 'desktop entry is missing exact line: %s\n' "$expected" >&2
        exit 1
    fi
done

if grep --extended-regexp '^(X-KDE-Shortcuts|StartupWMClass)=' "$desktop" >/dev/null; then
    printf 'desktop entry claims an upstream global shortcut or window class\n' >&2
    exit 1
fi

printf 'Konsole Custom exposes only its isolated executable and desktop entry\n'
