{
  kdePackages,
}:

kdePackages.konsole.overrideAttrs (oldAttrs: {
  patches = (oldAttrs.patches or [ ]) ++ [
    ../patches/0001-add-copy-entire-scrollback-action.patch
  ];

  passthru = (oldAttrs.passthru or { }) // {
    copyEntireScrollbackAction = true;
  };
})
