# code-owner: @agoose77
# This flake sets up a dev-shell that installs all the required
# packages for running deployer, and then installs the tool in the virtual environment
# It is not best-practice for the nix-way of distributing this code,
# but its purpose is to get an environment up and running.
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-helm.url = "github:NixOS/nixpkgs/9b100cfb67ccb2ff6e723b78d4ae2f9c88654a1c";
    dev-python = {
      url = "github:agoose77/dev-flakes/e0b0b96?dir=python";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = {
    self,
    nixpkgs,
    nixpkgs-helm,
    dev-python,
  }: let
    forAllSystems = nixpkgs.lib.genAttrs nixpkgs.lib.systems.flakeExposed;
  in {
    devShells = forAllSystems (system: let
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      # Additional nixpkgs for a particular package (helm)
      pkgs-helm = import nixpkgs-helm {
        inherit system;
      };

      # Define our interpreter
      python = pkgs.python313;
      gdk = pkgs.google-cloud-sdk.withExtraComponents (with pkgs.google-cloud-sdk.components; [
        gke-gcloud-auth-plugin
      ]);
      # Configure packages that need additional deps
      openstack = python.pkgs.toPythonApplication (
        python.pkgs.python-openstackclient.overridePythonAttrs (oldAttrs: {
          dependencies =
            (oldAttrs.dependencies or [])
            ++ [python.pkgs.python-magnumclient];
        })
      );
      # Configure the hook for enabling venvs
      # I think there's a way to auto-detect this, but
      # let's worry about that another time
      venvHook =
        dev-python.packages.${system}.nix-ld-venv-hook.override
        {python = python;};
      # Define our env packages (including the above)
      packages =
        [
          python
          venvHook
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
          # Dev deps
          jq
          yq-go
        ]);
      # Unset these unwanted env vars
      # PYTHONPATH bleeds from Nix Python packages
      unwantedEnvPreamble = ''
        unset SOURCE_DATE_EPOCH PYTHONPATH
      '';
    in {
      default = pkgs.mkShell {
        inherit packages;
        # Define additional input for patching interpreter

        venvDir = ".venv";

        # Drop bad env vars on activation
        postShellHook = unwantedEnvPreamble;

        # Setup venv by patching interpreter with LD_LIBRARY_PATH
        # This is required because ld does not exist on Nix systems
        postVenvCreation =
          # Install package
          ''
            ${unwantedEnvPreamble}
            pip install -e ".[dev]"
          '';
      };
    });
  };
}
