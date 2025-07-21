# code-owner: @agoose77
# This flake sets up an FSH dev-shell that installs all the required
# packages for running deployer, and then installs the tool in the virtual environment
# It is not best-practice for the nix-way of distributing this code,
# but its purpose is to get an environment up and running.
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      gdk = pkgs.google-cloud-sdk.withExtraComponents (with pkgs.google-cloud-sdk.components; [
        gke-gcloud-auth-plugin
      ]);
      python = pkgs.python313;
      pythonPackages = pkgs.python313Packages;
      envWithScript = script:
        (pkgs.buildFHSUserEnv {
          name = "2i2c-env";
          targetPkgs = pkgs:
            [
              python
              pkgs.pythonManylinuxPackages.manylinux2014Package
            ]
            ++ (with pythonPackages; [pip virtualenv])
            ++ (with pkgs; [
              cmake
              ninja
              gcc
              pre-commit
              # Infra packages
              go-jsonnet
              kubernetes-helm
              kubectl
              sops
              gdk
              awscli2
              azure-cli
              terraform
              eksctl
            ]);
          # If there is a higher power, why does it allow such horrible autoformatting below
          runScript = "${pkgs.writeShellScriptBin "runScript" (''
                               set -e
                               if [[ ! -d .venv ]]; then
                          __setup_env() {
                     tmp_path="$(mktemp -d)"
                    	  ${python.interpreter} -m venv "$tmp_path"
                                   "''${tmp_path}/bin/python" -m pip install -e .[dev]
              mv "$tmp_path" "''${PWD}/.venv"
                   }
                   __setup_env
                               fi
                               source .venv/bin/activate
                               set +e
            ''
            + script)}/bin/runScript";
        })
        .env;
    in {
      devShell = envWithScript "bash";
    });
}
