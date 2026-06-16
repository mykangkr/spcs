"""Database / connection layer.

`pool` is the one object the rest of the app should import:

    from db import pool

    with pool.connection() as conn:
        ...

Everything environment-specific (local SSO vs. SPCS service token) is hidden
inside `factory.get_connection()`. See SSO_connection_pooling.md for the why.
"""
from .pool import pool

__all__ = ["pool"]
