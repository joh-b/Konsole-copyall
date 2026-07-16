{
  kdePackages,
}:

kdePackages.konsole.overrideAttrs (oldAttrs: {
  prePatch = (oldAttrs.prePatch or "") + ''
    for modified_source in \
      src/session/SessionController.cpp \
      src/terminalDisplay/TerminalDisplay.cpp \
      src/terminalDisplay/TerminalDisplay.h
    do
      if ! grep -Fq 'SPDX-License-Identifier: GPL-2.0-or-later' "$modified_source"; then
        echo "unexpected or missing license on modified upstream file: $modified_source" >&2
        exit 1
      fi
    done
  '';

  patches = (oldAttrs.patches or [ ]) ++ [
    ../patches/0001-add-copy-entire-scrollback-action.patch
  ];

  passthru = (oldAttrs.passthru or { }) // {
    copyEntireScrollbackAction = true;
  };
})
