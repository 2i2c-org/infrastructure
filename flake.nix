# code-owner: @agoose77
# This flake sets up a dev-shell that installs all the required
# packages for running deployer, and then installs the tool in the virtual environment
# It is not best-practice for the nix-way of distributing this code,
# but its purpose is to get an environment up and running.
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs-helm.url = "github:NixOS/nixpkgs/9b100cfb67ccb2ff6e723b78d4ae2f9c88654a1c";
  };
  outputs = {
    self,
    nixpkgs,
    nixpkgs-helm,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      pkgs-helm = import nixpkgs-helm {
        inherit system;
      };
      inherit (pkgs) lib;

      gdk = pkgs.google-cloud-sdk.withExtraComponents (with pkgs.google-cloud-sdk.components; [
        gke-gcloud-auth-plugin
      ]);
      openstack = python.pkgs.toPythonApplication (
        python.pkgs.python-openstackclient.overridePythonAttrs (oldAttrs: {
          dependencies =
            (oldAttrs.dependencies or [])
            ++ [python.pkgs.python-magnumclient];
        })
      );
      python = pkgs.python313;
      packages =
        [
          python
          python.pkgs.venvShellHook
        ]
        ++ (with pkgs; [
          cmake
          ninja
          gcc
          pre-commit
          # Infra packages
          age
          go-jsonnet
          pkgs-helm.kubernetes-helm
          kubectl
          sops
          gdk
          awscli2
          azure-cli
          terraform
          openstack
          eksctl
        ]);
      env = lib.optionalAttrs pkgs.stdenv.isLinux {
        # Python uses dynamic loading for certain libraries.
        # We'll set the linker path instead of patching RPATH
        LD_LIBRARY_PATH = lib.makeLibraryPath pkgs.pythonManylinuxPackages.manylinux2014;
      };
    in {
      devShell = pkgs.mkShell {
        inherit env packages;

        venvDir = "./.venv";
        postShellHook = ''
          unset SOURCE_DATE_EPOCH PYTHONPATH
        '';
        postVenvCreation = ''
          unset SOURCE_DATE_EPOCH PYTHONPATH
          pip install -e ".[dev]"
        '';
      };
    });
}
