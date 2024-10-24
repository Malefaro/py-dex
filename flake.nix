{
  description = "Dev environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils,...  }@inputs:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          pkgs = import nixpkgs {
            inherit system; config.allowUnfree = true;
          };


          extraInputs = if pkgs.stdenv.isDarwin then [
              # extra inputs for darwin
              pkgs.darwin.apple_sdk.frameworks.SystemConfiguration
              pkgs.darwin.apple_sdk.frameworks.CoreFoundation
              pkgs.darwin.apple_sdk.frameworks.CoreServices
              pkgs.darwin.apple_sdk.frameworks.Security
              pkgs.libz
          ] else [];

        in
        {
          devShells.default = with pkgs; mkShell {
            buildInputs = [
              (python311.withPackages (python-pkgs: [
                # extra pkgs here
              ]))
              nodePackages.pyright # python lsp
              poetry


            ] ++ extraInputs;
            shellHook = ''
              # workaround for jupyter-lab `ImportError: libstdc++.so.6`
              export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
                  pkgs.stdenv.cc.cc
              ]}:$LD_LIBRARY_PATH
            '';
          };
        }
      );
}

