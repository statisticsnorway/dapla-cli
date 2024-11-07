{
  description = "Package and dev environment for the dapla-cli";

  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs @ {
    flake-parts,
    poetry2nix,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = ["x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin"];
      perSystem = {
        config,
        self',
        inputs',
        pkgs,
        system,
        ...
      }: {
        devShells.default = pkgs.mkShell {
          name = "dapla-lab";
          packages = with pkgs; [
            python3
            poetry
            ruff-lsp
          ];
        };
        formatter = pkgs.alejandra;
        packages.dapla-cli = let
          inherit (poetry2nix.lib.mkPoetry2Nix {inherit pkgs;}) mkPoetryApplication overrides;
        in
          mkPoetryApplication {
            projectDir = ./.;
            overrides = overrides.withDefaults (final: prev: {
              ruff = prev.ruff.override {preferWheel = true;};
              ruamel-yaml-clib = null;
              sphinx-click = null;
              furo = null;
            });
          };

        packages.default = self'.packages.dapla-cli;
      };
    };
}
