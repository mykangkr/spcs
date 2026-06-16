"""The ONLY place that knows whether we're running locally or inside SPCS.

`get_connection()` opens a single Snowflake connection with the correct
authentication for the current environment. It does NOT pool — the pool
(pool.py) calls this whenever it needs a fresh connection.

Two environments, two auth flows (see SSO_connection_pooling.md):

  * Local dev  -> externalbrowser SSO (a browser popup logs you in).
  * SPCS       -> owner's rights via the service's OAuth token file, which
                  Snowflake injects at /snowflake/session/token and rotates
                  roughly every 10 minutes. We re-read the file on every new
                  connection so rotation is handled automatically.
"""
import os
from pathlib import Path

from snowflake.connector import connect
from snowflake.connector.connection import SnowflakeConnection

# SPCS mounts the service's OAuth token here. Its presence is how we detect SPCS.
OAUTH_TOKEN_PATH = Path("/snowflake/session/token")


def _in_spcs() -> bool:
    """True when running inside an SPCS container (the token file exists)."""
    return OAUTH_TOKEN_PATH.exists()


def _common_params() -> dict:
    """Session context shared by both environments."""
    return dict(
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("SNOWFLAKE_DATABASE"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA"),
        role=os.environ.get("SNOWFLAKE_ROLE"),
    )


def get_connection() -> SnowflakeConnection:
    """Open ONE Snowflake connection using the right auth for the environment.

    Callers should not use this directly for request handling — go through
    `pool.connection()` so connections are reused. This is also where you'd
    branch to caller's-rights auth (a per-user token) if you ever need
    Snowflake to enforce per-user RBAC instead of the app doing authz.
    """
    if _in_spcs():
        # SPCS: owner's rights via the service's OAuth token.
        # Re-reading the file each call keeps NEW connections rotation-safe.
        return connect(
            host=os.environ["SNOWFLAKE_HOST"],         # injected by SPCS
            account=os.environ["SNOWFLAKE_ACCOUNT"],   # injected by SPCS
            authenticator="oauth",
            token=OAUTH_TOKEN_PATH.read_text().strip(),
            client_session_keep_alive=True,
            **_common_params(),
        )

    # Local dev: SSO browser login. Swap for key-pair auth if you prefer
    # a non-interactive local flow (authenticator + private_key).
    return connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser",
        **_common_params(),
    )
