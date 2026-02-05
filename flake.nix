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

      # Configure packages that need additional deps
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
      # Define our interpreter
      python = pkgs.python313;
      manyLinux = pkgs.pythonManylinuxPackages.manylinux2014;

      # Define our env packages (including the above)
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
    in {
      devShell = let
        # Unset these unwanted env vars
        # PYTHONPATH bleeds from Nix Python packages
        unwantedEnvPreamble = ''
          unset SOURCE_DATE_EPOCH PYTHONPATH
        '';
      in
        pkgs.mkShell rec {
          inherit packages;
          # Define additional input for patching interpreter
          nativeBuildInputs = [pkgs.makeWrapper];

          venvDir = ".venv";

          # Drop bad env vars on activation
          postShellHook = unwantedEnvPreamble;

          # Setup venv by patching interpreter with LD_LIBRARY_PATH
          # This is required because ld does not exist on Nix systems
          postVenvCreation = let
            # Find the interpreter of the venv
            interpreterSubPath = lib.path.subpath.join ["bin" (baseNameOf python.interpreter)];
          in
            unwantedEnvPreamble
            # Patch the venv to find the dynamic libs
            + ''
              wrapProgram "$VIRTUAL_ENV/${interpreterSubPath}" --prefix "LD_LIBRARY_PATH" : "${lib.makeLibraryPath manyLinux}"
            ''
            +
            # Install package
            ''
              pip install -e ".[dev]"
            '';
        };
    });
}
