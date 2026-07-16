{
  fetchurl,
  kdePackages,
}:

let
  upstream = builtins.fromJSON (builtins.readFile ./upstream.json);
in
kdePackages.konsole.overrideAttrs (oldAttrs: {
  version = upstream.version;

  src = fetchurl {
    inherit (upstream) url hash;
  };

  prePatch = (oldAttrs.prePatch or "") + ''
    for modified_source in \
      src/main.cpp \
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
    ../patches/0002-use-konsole-custom-identity.patch
  ];

  passthru = (oldAttrs.passthru or { }) // {
    copyEntireScrollbackAction = true;
    inherit upstream;
  };
})
