{
  description = "wanderers W-Corne layout — Vial GUI, generator and probe";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      py = pkgs.python3;
      script =
        name: file:
        pkgs.writeShellScriptBin name ''
          cd "${self}" || exit 1
          exec ${py}/bin/python3 ${file} "$@"
        '';
    in
    {
      packages.${system} = {
        vial = pkgs.vial;
        default = pkgs.vial;
        probe = script "wcorne-probe" "probe/vialq2.py";
      };

      apps.${system} = {
        # nix run .#vial   — the Vial GUI (needs the hidraw udev rule, see README)
        vial = {
          type = "app";
          program = "${pkgs.vial}/bin/Vial";
        };
        default = self.apps.${system}.vial;
        # nix run .#probe  — dump the board's Vial budget + definition (replug dongle first)
        probe = {
          type = "app";
          program = "${self.packages.${system}.probe}/bin/wcorne-probe";
        };
      };

      # nix develop — python3 for `python3 layout.py`, xkbcli for compiling the
      # xkb option, Vial on PATH.
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          py
          pkgs.vial
          pkgs.libxkbcommon # xkbcli compile-keymap
        ];
        shellHook = ''
          echo "wanderers W-Corne: python3 layout.py | Vial | xkbcli compile-keymap --include ./xkb --include-defaults --layout us --variant dvorak-alt-intl --options compose:menu,wanderers:magic"
        '';
      };
    };
}
