import os
from contextlib import contextmanager


@contextmanager
def unset_env_vars(vars):
    """
    Temporarily unset env vars in vars if they exist
    """
    orig_values = {}
    for e in vars:
        if e in os.environ:
            orig_values[e] = os.environ[e]
            # Clear values from os.environ if they are present!
            del os.environ[e]

    try:
        yield
    finally:
        for e in orig_values:
            # Put values back into os.environ when contextmanager returns
            os.environ[e] = orig_values[e]
