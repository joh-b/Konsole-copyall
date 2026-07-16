#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later

set -euo pipefail

if (( $# != 1 )); then
    printf 'usage: %s KONSOLE_STORE_PATH\n' "$0" >&2
    exit 2
fi

result=$1

if [[ ! -x "$result/bin/konsole" ]]; then
    printf 'Konsole executable not found in %s\n' "$result" >&2
    exit 1
fi

for marker in 'copy-entire-scrollback' 'Copy Entire Scrollback'; do
    if ! grep --recursive --binary-files=text --files-with-matches \
        --fixed-strings -- "$marker" "$result" >/dev/null; then
        printf 'built package does not contain marker: %s\n' "$marker" >&2
        exit 1
    fi
done

printf 'Built Konsole contains the copy-all action markers\n'
