# SSO Authentication & Connection Pooling (Local + SPCS)

This document explains how our FastAPI backend authenticates to Snowflake and
manages connections — both on a developer laptop and when deployed inside
Snowpark Container Services (SPCS). It records *why* we made these choices, not
just what the code does.

> Target runtime: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2`

---

## 1. The two identities in SPCS

When a request reaches our service running in SPCS, **two separate
authentications have already happened**, giving us two identities to choose
from when we run SQL:

| Layer | Who it represents | Where we get it | Lifetime |
|-------|-------------------|-----------------|----------|
| **Service token** | the service's own role (the "service account") | file at `/snowflake/session/token` | rotated ~every 10 min |
| **User token** | the human who logged in via SSO at the ingress | HTTP headers on the request | short-lived, per request |

On every request the SPCS ingress injects headers we can read:

- `Sf-Context-Current-User` — the username (e.g. `MIYAE`)
- `Sf-Context-Current-User-Token` — a token that can authenticate to Snowflake
  **as that user**

This is the key insight: SPCS hands us *both* a service identity and the
calling user's identity. Which one runs the query is an architectural decision.

---

## 2. Owner's rights vs. caller's rights

### Owner's rights (what we use)

Connect with the **service token**. Every query runs as the service role.
We read `Sf-Context-Current-User` only to know *who is asking*, and **our app
code** enforces what they may see (e.g. `WHERE owner = :current_user`).

- One connection pool, shared by all users.
- Snowflake sees a single identity.
- Authorization logic lives in our application.

### Caller's rights (the alternative)

Take `Sf-Context-Current-User-Token` from the request header and build the
connection from **that**. The query then runs **as the logged-in user**, so
Snowflake's own RBAC, row-access policies, and audit logging apply
automatically.

- A different user means a different connection — **you cannot share one pool
  across users** (at most, a pool per user).
- Authorization is enforced by Snowflake, not the app.

### Our choice and why

We use **owner's rights + a shared pool**. For an internal app this is simpler,
pools cleanly, and we want the application to control authorization anyway.

Switch to caller's rights **only** if a requirement says: *"Snowflake must
enforce per-user table grants"* or *"we need per-user activity in Snowflake's
audit logs."* The branch point for that is `db/factory.get_connection()`.

```python
# Caller's-rights sketch (NOT what we do today) — per request, per user:
from fastapi import Request
from snowflake.connector import connect

def connect_as_caller(request: Request):
    user_token = request.headers["Sf-Context-Current-User-Token"]
    return connect(
        host=os.environ["SNOWFLAKE_HOST"],
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        authenticator="oauth",
        token=user_token,          # the user, not the service
    )
```

---

## 3. Why a connection pool (not the two extremes)

We deliberately avoid both ends of the spectrum:

**Not "open/close a connection per request."**
A Snowflake login + OAuth handshake costs hundreds of milliseconds. Paying that
on every request wastes latency and resources.

**Not "one eternal global connection."**
- The Snowflake connector is blocking and a single connection is **not safe to
  share across threads**. FastAPI runs `def` routes in a threadpool, so
  concurrent requests would collide on one connection.
- A single connection serializes all work and can silently drop with no
  recovery path.

**So: a small pool with a health check + reconnect.** We get the reuse benefit
of long-lived connections without the thread-safety and dead-connection
failure modes. See `db/pool.py`.

### The health-check trade-off

`pool._acquire()` runs a `SELECT 1` to confirm a borrowed connection is still
alive before handing it out. This is one extra round-trip per request — the
bulletproof option. If that latency ever matters, optimize by pinging only
after a connection has been idle for some threshold instead of every time.

### Token rotation is handled for free

An **already-open** connection stays authenticated even after the service token
file rotates — the session is established. Only **new** connections need the
fresh token, and `get_connection()` re-reads `/snowflake/session/token` every
time it opens one. So a long-lived pool is rotation-safe with no extra work.

---

## 4. The `--workers 2` reality

This is the most important operational detail and the one most easily missed.

`pool = SnowflakeConnectionPool(size=4)` is a **module-level object created once
per worker process.** With `--workers 2`:

```
worker process #1  ->  its own pool (up to 4 connections)
worker process #2  ->  its own pool (up to 4 connections)
                       ------------------------------------
                       up to 8 Snowflake connections total
```

Processes share nothing in memory, so **"one session for all users" is never
literally true.** When reasoning about warehouse load or connection limits,
always multiply pool size by the worker count.

To change the total, tune either knob: `size=` in `db/pool.py` or `--workers`.

---

## 5. Local vs. SPCS — what actually differs

Only **one function** knows the difference: `db/factory.get_connection()`.
Everything above it (the pool, the services, the routes) is identical in both
environments.

| | Local dev | SPCS |
|--|-----------|------|
| Detection | token file absent | `/snowflake/session/token` exists |
| Auth | `authenticator="externalbrowser"` (SSO popup) | `authenticator="oauth"` + token file |
| Identity | your user | the service role (owner's rights) |
| Host/account | from env vars | injected by SPCS |

### Environment variables

Both environments read session context from the environment:

```
SNOWFLAKE_ACCOUNT     # required
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
SNOWFLAKE_SCHEMA
SNOWFLAKE_ROLE
```

Local-only:

```
SNOWFLAKE_USER        # your username for the externalbrowser SSO flow
```

SPCS-only (injected by the platform, you don't set these yourself):

```
SNOWFLAKE_HOST
SNOWFLAKE_ACCOUNT
```

For non-interactive local runs, swap `externalbrowser` for key-pair auth
(`authenticator` + `private_key`) in `get_connection()`.

---

## 6. Backend toggle (SQLite ↔ Snowflake)

We keep both data backends in the tree and pick one at startup with a single
environment variable, so local dev keeps working with zero setup while the
Snowflake path is ready to switch on.

```
TASK_BACKEND unset / anything   -> SQLite   (services/task_service.py)
TASK_BACKEND=snowflake          -> Snowflake (services/task_service_snowflake.py)
```

The switch is defined in exactly one place, `services/backend.py`, which
exports the chosen module as `service`. Everyone imports from there:

```python
# routers/tasks.py
from services.backend import service as task_service

# main.py
from services.backend import service
service.init_db()        # follows the selected backend, not hard-coded to SQLite
```

Because the Snowflake module is only imported when selected, `snowflake-
connector-python` is **not** required to run the SQLite default — handy before
the dependency is installed or while migrating.

To run against Snowflake:

```bash
pip install -r requirements.txt
# set the env vars from §5, then:
TASK_BACKEND=snowflake uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

Unset `TASK_BACKEND` to fall back to SQLite at any time.

---

## 7. Code map

| File | Responsibility |
|------|----------------|
| `backend/db/factory.py` | `get_connection()` — the only env-aware code; local vs. SPCS auth |
| `backend/db/pool.py` | `SnowflakeConnectionPool` + the shared `pool` instance (one per worker) |
| `backend/db/__init__.py` | re-exports `pool` so callers do `from db import pool` |
| `backend/services/backend.py` | reads `TASK_BACKEND`, exports the active `service` module |
| `backend/services/task_service.py` | SQLite backend (default) |
| `backend/services/task_service_snowflake.py` | Snowflake backend (pooled) |
| `backend/main.py` | FastAPI `lifespan` closes the pool on shutdown; runs `service.init_db()` |
| `backend/routers/tasks.py` | HTTP routes; calls the selected `service` |

### Usage pattern

```python
from db import pool
from snowflake.connector import DictCursor

def list_tasks():
    with pool.connection() as conn:        # borrow; auto-returned on block exit
        cur = conn.cursor(DictCursor)
        cur.execute("SELECT id, text, done, priority FROM tasks")
        return [...]                        # map rows to your model
```
