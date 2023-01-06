#!/usr/bin/env python3
"""
Simple utility to decrypt secrets sent to `support@2i2c.org` via `age`
"""
import argparse
import pathlib
import subprocess
import sys
import tempfile
from contextlib import contextmanager


@contextmanager
def decrypt_age_private_key():
    """
    Decrypt our age private key, which is encrypted with sops
    """
    age_private_key = pathlib.Path(__file__).parent.joinpath("enc-age-private.key")

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


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "encrypted_file",
        nargs="?",
        help="Path to age-encrypted file sent by user. Leave empty to read from stdin",
    )
    args = argparser.parse_args()

    if not args.encrypted_file:
        # No file specified
        print("Paste the encrypted file contents, hit enter and then press Ctrl+D")
        encrypted_contents = sys.stdin.read().encode()
    else:
        # rb so it doesn't try to decode to utf-8, in case we have a non-armored file
        with open(args.encrypted_file, "rb") as f:
            encrypted_contents = f.read()

    decrypt_content(encrypted_contents)


main()
