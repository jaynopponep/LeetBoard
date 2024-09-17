{
  description = "dev shell for LeetBoard discord bot";

  inputs = { nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable"; };

  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        nativeBuildInputs = with pkgs; [
          python312Packages.python
          python312Packages.pip
          python312Packages.discordpy
          python312Packages.playwright
          python312Packages.requests
          # playwright packages
          playwright-driver.browsers
        ];
        shellHook = "	
          source \"$PWD/.env\" || exit 1	\n 
          export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
          export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
        ";
      };
    };
}
