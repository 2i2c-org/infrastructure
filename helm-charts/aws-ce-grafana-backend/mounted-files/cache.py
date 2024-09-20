"""
It seems Python doesn't provide a built in way to cache function calls, so this
implements an answer from stackoverflow by user McToel from
https://stackoverflow.com/a/73026174/2220152.

A limitation of this is implementation is that it can't be used on functions
accepting lists etc, even if the functions we have only have lists with hashable
content that could be compared and concluded equal.
"""

import time
from functools import lru_cache


def ttl_lru_cache(seconds_to_live: int, maxsize: int = 128):
    """
    Time aware lru caching
    """

    def wrapper(func):

        @lru_cache(maxsize)
        def inner(__ttl, *args, **kwargs):
            # Note that __ttl is not passed down to func,
            # as it's only used to trigger cache miss after some time
            return func(*args, **kwargs)

        return lambda *args, **kwargs: inner(
            time.time() // seconds_to_live, *args, **kwargs
        )

    return wrapper
