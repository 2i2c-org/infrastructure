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
      envWithScript = script:
        (pkgs.buildFHSUserEnv {
          name = "2i2c-env";
          targetPkgs = pkgs: (with pkgs; [
            python313
            python313Packages.pip
            python313Packages.virtualenv
            pythonManylinuxPackages.manylinux2014Package
            cmake
            ninja
            gcc
            pre-commit
            # Infra packages
            go-jsonnet
            helm
            kubectl
            sops
            gdk
            awscli2
            azure-cli
            terraform
            eksctl
          ]);
          runScript = "${pkgs.writeShellScriptBin "runScript" (''
              set -e
              if [[ ! -d .venv ]]; then
                ${pkgs.python3.interpreter} -m venv .venv
                source .venv/bin/activate
                python -m pip install -e .[dev]
              else
                source .venv/bin/activate
              fi
              set +e
            ''
            + script)}/bin/runScript";
        })
        .env;
    in {
      devShell = envWithScript "bash";
    });
}
