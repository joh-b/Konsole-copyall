{
  description = "Konsole with a native Copy Entire Scrollback action";

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
          konsoleCopyall = pkgs.callPackage ./nix/package.nix { };
        in
        {
          "konsole-copy-entire-scrollback" = konsoleCopyall;
          default = konsoleCopyall;
        }
      );

      checks = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          package = self.packages.${system}.default;
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

          built-action = pkgs.runCommand "verify-konsole-copyall-binary" {
            nativeBuildInputs = [
              pkgs.bash
              pkgs.gnugrep
            ];
          } ''
            ${pkgs.bash}/bin/bash ${./tests/verify-built-action.sh} ${package}
            touch "$out"
          '';
        }
      );

      formatter = forAllSystems (system: (import nixpkgs { inherit system; }).nixfmt);
    };
}
