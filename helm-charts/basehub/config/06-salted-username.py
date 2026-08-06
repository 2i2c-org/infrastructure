# Allow anonymizing username to not store *any* PII
import base64
import hashlib
import json
import os

from z2jh import get_config


def salt_username(authenticator, handler, auth_model):
    # Combine parts of user info with different provenances to eliminate
    # possible deanonym attacks when things get leaked.

    # FIXME: Provide useful error message when using an auth provider that
    # doesn't give us 'oidc'
    # FIXME: Raise error if this is attempted to be used with anything other than CILogon
    USERNAME_DERIVATION_PEPPER = bytes.fromhex(os.environ["USERNAME_DERIVATION_PEPPER"])
    cilogon_user = auth_model["auth_state"]["cilogon_user"]
    user_key_parts = {
        # Opaque ID from CILogon
        "sub": cilogon_user["sub"],
        # Combined together, opaque ID from upstream IDP (GitHub, Google, etc)
        "idp": cilogon_user["idp"],
        "oidc": cilogon_user["oidc"],
    }

    # Use JSON here, so we don't have to deal with picking a string
    # delimiter that will not appear in any of the parts.
    # keys are sorted to ensure stable output over time
    user_key = json.dumps(user_key_parts, sort_keys=True).encode("utf-8")

    # The cryptographic choices made here are:
    # - Use blake2, because it's fairly modern
    # - Set blake2 to output 32 bytes as output, which is good enough for our use case
    # - Use base32 encoding, as it will produce maximum of 56 characters
    #   for 32 bytes output by blake2. We have 63 character username
    #   limits in many parts of our code (particularly, in usernames
    #   being part of labels in kubernetes pods), so this helps
    # - Convert everything to lowercase, as base64.b32encode produces
    #   all uppercase characters by default. Our usernames are preferably
    #   lowercase, as uppercase characters must be encoded for kubernetes'
    #   sake
    # - strip the = padding provided by base64.b32encode. This is present
    #   primarily to be able to determine length of the original byte
    #   sequence accurately. We don't care about that here. Also = is
    #   encoded in kubernetes and puts us over the 63 char limit.
    # - Use blake2 here explicitly as a keyed hash, rather than use
    #   hmac. This is the canonical way to do this, and helps make it
    #   clearer that we want it to output 32byte hashes. We could have
    #   used a 16byte hash here for shorter usernames, but it is unclear
    #   what that does to the security properties. So better safe than
    #   sorry, and stick to 32bytes (rather than the default 64)
    digested_user_key = (
        base64.b32encode(
            hashlib.blake2b(
                user_key, key=USERNAME_DERIVATION_PEPPER, digest_size=32
            ).digest()
        )
        .decode("utf-8")
        .lower()
        .rstrip("=")
    )

    # Replace the default name with our digested name, thus
    # discarding the default name
    auth_model["name"] = digested_user_key

    return auth_model


if get_config("custom.auth.anonymizeUsername", False):
    # https://jupyterhub.readthedocs.io/en/stable/reference/api/auth.html#jupyterhub.auth.Authenticator.post_auth_hook
    c.Authenticator.post_auth_hook = salt_username
