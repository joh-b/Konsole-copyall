{
  description = "An isolated Konsole Custom launcher with a native Copy Entire Scrollback action";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs =
    {
      self,
      nixpkgs,
    }:
    let
      supportedSystems = [ "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          patchedKonsole = pkgs.callPackage ./nix/package.nix { };
          konsoleCustom = pkgs.callPackage ./nix/konsole-custom.nix {
            inherit patchedKonsole;
          };
        in
        {
          "patched-konsole" = patchedKonsole;
          "konsole-copy-entire-scrollback" = patchedKonsole;
          "konsole-custom" = konsoleCustom;
          default = konsoleCustom;
        }
      );

      checks = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          package = self.packages.${system}.default;
          patchedKonsole = self.packages.${system}."patched-konsole";
        in
        {
          inherit package;

          patch-content = pkgs.runCommand "verify-konsole-copyall-patch" {
            nativeBuildInputs = [ pkgs.python3 ];
          } ''
            python3 ${./tests/verify-patch-content.py} \
              ${./patches/0001-add-copy-entire-scrollback-action.patch}
            touch "$out"
          '';

          identity-patch-content = pkgs.runCommand "verify-konsole-custom-identity-patch" {
            nativeBuildInputs = [ pkgs.python3 ];
          } ''
            python3 ${./tests/verify-identity-patch.py} \
              ${./patches/0002-use-konsole-custom-identity.patch}
            touch "$out"
          '';

          built-action = pkgs.runCommand "verify-konsole-copyall-binary" {
            nativeBuildInputs = [
              pkgs.bash
              pkgs.binutils
              pkgs.findutils
              pkgs.gnugrep
            ];
          } ''
            ${pkgs.bash}/bin/bash ${./tests/verify-built-action.sh} ${patchedKonsole}
            touch "$out"
          '';

          public-interface = pkgs.runCommand "verify-konsole-custom-public-interface" {
            nativeBuildInputs = [
              pkgs.desktop-file-utils
              pkgs.findutils
              pkgs.gnugrep
            ];
          } ''
            ${pkgs.bash}/bin/bash ${./tests/verify-public-interface.sh} \
              ${package} ${patchedKonsole}
            touch "$out"
          '';

          upstream-tracker = pkgs.runCommand "verify-konsole-upstream-tracker" {
            nativeBuildInputs = [ pkgs.python3 ];
          } ''
            SELECTOR_SCRIPT=${./scripts/select_latest_stable_tag.py} \
              python3 ${./tests/test-select-latest-stable-tag.py}
            python3 ${./tests/verify-upstream-metadata.py} \
              ${./nix/upstream.json}
            python3 ${./tests/verify-upstream-workflow.py} \
              ${./.github/workflows/upstream-release.yml} \
              ${./.github/workflows/publish.yml}
            touch "$out"
          '';

          nixos-maintenance = pkgs.runCommand "verify-nixos-stable-maintenance" {
            nativeBuildInputs = [ pkgs.python3 ];
          } ''
            python3 ${./tests/test-select-latest-nixos-stable.py}
            python3 ${./tests/test-update-nixos-stable.py}
            python3 ${./tests/verify-nixos-maintenance.py} \
              ${./renovate.json} \
              ${./.github/workflows/nixos-stable.yml} \
              ${./flake.nix} \
              ${./.github/workflows/compatibility.yml}
            touch "$out"
          '';
        }
      );

      formatter = forAllSystems (system: (import nixpkgs { inherit system; }).nixfmt);
    };
}
