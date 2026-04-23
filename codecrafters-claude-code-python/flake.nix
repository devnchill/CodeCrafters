{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {

        packages = with pkgs; [
          codecrafters-cli
          nil
          nixfmt

          uv
          pyright
          ruff

          python314
        ];
        shellHook = ''
          					export UV_PYTHON_DOWNLOADS=never
                    				'';
      };
    };
}
