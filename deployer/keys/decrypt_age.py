"""
Simple utility to decrypt secrets sent to `support@2i2c.org` via `age`
"""
import pathlib
import subprocess
import sys
import tempfile
from contextlib import contextmanager

import typer

from ..cli_app import app


@contextmanager
def decrypt_age_private_key():
    """
    Decrypt our age private key, which is encrypted with sops
    """
    age_private_key = pathlib.Path(__file__).parent.joinpath(
        "enc-age-secret-private.key"
    )

    with tempfile.NamedTemporaryFile() as f:
        subprocess.check_call(
            ["sops", "--output", f.name, "--decrypt", age_private_key]
        )

        yield f.name


def decrypt_content(encrypted_contents):
    """
    Decrypt contents
    """
    with decrypt_age_private_key() as age_key:
        cmd = ["age", "--decrypt", "--identity", age_key]

        subprocess.run(cmd, input=encrypted_contents, check=True)


@app.command()
def decrypt_age(
    encrypted_file_path: str = typer.Option(
        "",
        help="Path to age-encrypted file sent by user. Leave empty to read from stdin.",
    )
):
    """Decrypt secrets sent to `support@2i2c.org` via `age`"""
    if not encrypted_file_path:
        # No file specified
        print("Paste the encrypted file contents, hit enter and then press Ctrl+D")
        encrypted_contents = sys.stdin.read().encode()
    else:
        # rb so it doesn't try to decode to utf-8, in case we have a non-armored file
        with open(encrypted_file_path, "rb") as f:
            encrypted_contents = f.read()

    decrypt_content(encrypted_contents)
