{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {

  # add binaries
  packages = with pkgs.python312Packages; [
    openpyxl
    pandas
  ];

  # add build dependecies from list of derivations
  # inputsFrom = with pkgs; [
    
  # ];

#   # bash statements executed by nix-shell
#   shellHook = ''
#   export DEBUG=1;
# '';
}
