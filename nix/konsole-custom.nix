{
  lib,
  makeWrapper,
  patchedKonsole,
  runCommand,
}:

runCommand "konsole-custom-${patchedKonsole.version}"
  {
    nativeBuildInputs = [ makeWrapper ];
    inherit (patchedKonsole) version;

    meta = (patchedKonsole.meta or { }) // {
      description = "Isolated Konsole launcher with a native Copy Entire Scrollback action";
      mainProgram = "konsole-custom";
    };

    passthru = {
      inherit patchedKonsole;
      copyEntireScrollbackAction = true;
      upstream = patchedKonsole.upstream;
    };
  }
  ''
    mkdir -p "$out/bin" "$out/share/applications"

    makeWrapper \
      ${lib.getExe' patchedKonsole "konsole"} \
      "$out/bin/konsole-custom" \
      --prefix XDG_DATA_DIRS : "$out/share"

    substitute \
      ${./org.kde.konsole-custom.desktop} \
      "$out/share/applications/org.kde.konsole-custom.desktop" \
      --replace-fail '@out@' "$out"
  ''
