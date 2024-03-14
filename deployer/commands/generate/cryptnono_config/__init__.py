import shutil
import subprocess
from pathlib import Path

from deployer.cli_app import generate_app
from deployer.utils.file_acquisition import REPO_ROOT_PATH

HERE = Path(__file__).parent


@generate_app.command()
def cryptnono_secret_config():
    """
    Update the secret blocklist for cryptnono
    """
    unencrypted_path = HERE / "unencrypted_secret_blocklist.py"

    try:
        # The code to generate this blocklist is small but encrypted.
        # We temporarily decrypt it before importing the file via regular means,
        # and then delete the imported file.
        shutil.copyfile(HERE / "enc-blocklist-generator.secret.py", unencrypted_path)
        subprocess.check_call(
            ["sops", "--decrypt", "--in-place", str(unencrypted_path)]
        )

        from .unencrypted_secret_blocklist import write_encrypted_cryptnono_config

        secret_config_path = (
            REPO_ROOT_PATH / "helm-charts/support/enc-cryptnono.secret.values.yaml"
        )
        write_encrypted_cryptnono_config(secret_config_path)
    finally:
        unencrypted_path.unlink()
