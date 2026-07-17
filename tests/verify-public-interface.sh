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

if ! grep --fixed-strings -- "$result/share" "$executable" >/dev/null; then
    printf 'custom executable does not expose its desktop resources through XDG_DATA_DIRS\n' >&2
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

declare -A desktop_values=()
declare -A desktop_value_counts=()
section=
while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
        \[*\])
            section=${line:1:${#line}-2}
            ;;
        ''|'#'*|';'*)
            ;;
        *=*)
            key=${line%%=*}
            value=${line#*=}
            composite_key="$section"$'\034'"$key"
            desktop_values["$composite_key"]=$value
            desktop_value_counts["$composite_key"]=$(( ${desktop_value_counts["$composite_key"]:-0} + 1 ))
            ;;
    esac
done < "$desktop"

assert_desktop_value() {
    local expected_section=$1
    local expected_key=$2
    local expected_value=$3
    local composite_key="$expected_section"$'\034'"$expected_key"
    local count=${desktop_value_counts["$composite_key"]:-0}
    local actual=${desktop_values["$composite_key"]:-}

    if (( count != 1 )) || [[ "$actual" != "$expected_value" ]]; then
        printf 'desktop [%s] must contain exactly %s=%s (found count=%d, value=%s)\n' \
            "$expected_section" "$expected_key" "$expected_value" "$count" "$actual" >&2
        exit 1
    fi
}

assert_desktop_value 'Desktop Entry' 'Type' 'Application'
assert_desktop_value 'Desktop Entry' 'TryExec' "$executable"
assert_desktop_value 'Desktop Entry' 'Exec' "$executable"
assert_desktop_value 'Desktop Entry' 'Actions' 'NewWindow;NewTab;'
assert_desktop_value 'Desktop Action NewWindow' 'Exec' "$executable"
assert_desktop_value 'Desktop Action NewTab' 'Exec' "$executable --new-tab"

new_tab_references=0
for value in "${desktop_values[@]}"; do
    if [[ "$value" == *--new-tab* ]]; then
        (( new_tab_references += 1 ))
    fi
done
if (( new_tab_references != 1 )); then
    printf 'desktop entry must reference --new-tab exactly once, in its NewTab action\n' >&2
    exit 1
fi

if grep --extended-regexp '^(X-KDE-Shortcuts|StartupWMClass)=' "$desktop" >/dev/null; then
    printf 'desktop entry claims an upstream global shortcut or window class\n' >&2
    exit 1
fi

printf 'Konsole Custom exposes only its isolated executable and desktop entry\n'
