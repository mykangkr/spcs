"""A small, thread-safe Snowflake connection pool.

Why a pool and not (a) one global connection or (b) open/close per request:

  * The Snowflake connector is blocking and a single connection is NOT safe to
    share across threads. FastAPI runs `def` routes in a threadpool, so we need
    one connection per concurrent request -> a small pool.
  * Opening a connection costs a login + OAuth handshake (hundreds of ms).
    Doing that per request is wasteful, so we reuse connections.
  * One eternal connection serializes everything and can silently die. A pool
    with a health check and reconnect gives us reuse WITHOUT those failure modes.

IMPORTANT about `uvicorn --workers 2`: the module-level `pool` below is created
once PER worker PROCESS. Two workers = two independent pools = up to 2 * size
connections total. Processes share nothing, so "one session for all users" is
never literally true — size the pool per worker and multiply by worker count
when reasoning about warehouse load. See SSO_connection_pooling.md.
"""
import contextlib
import queue
import threading

from .factory import get_connection


class SnowflakeConnectionPool:
    def __init__(self, size: int = 4):
        self._size = size
        self._free: queue.Queue = queue.Queue(maxsize=size)
        self._lock = threading.Lock()
        self._created = 0

    def _acquire(self):
        # Reuse a free connection if there is one; otherwise create one while
        # we're still under the cap; otherwise block until someone releases.
        try:
            conn = self._free.get_nowait()
        except queue.Empty:
            with self._lock:
                if self._created < self._size:
                    self._created += 1
                    return get_connection()
            conn = self._free.get()  # at cap -> wait for a free connection

        # Health check: a pooled connection may have dropped since last use.
        # Trade-off: this "SELECT 1" is one round-trip per acquire. It's the
        # bulletproof option; optimize later by pinging only after idle time.
        if not self._alive(conn):
            with contextlib.suppress(Exception):
                conn.close()
            conn = get_connection()
        return conn

    @staticmethod
    def _alive(conn) -> bool:
        if conn.is_closed():
            return False
        try:
            conn.cursor().execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    def _release(self, conn):
        try:
            self._free.put_nowait(conn)
        except queue.Full:
            conn.close()  # more connections alive than the pool wants -> drop it

    @contextlib.contextmanager
    def connection(self):
        """Borrow a connection for the duration of a `with` block.

            with pool.connection() as conn:
                cur = conn.cursor()
                cur.execute(...)
        """
        conn = self._acquire()
        try:
            yield conn
        finally:
            self._release(conn)

    def close_all(self):
        """Close every pooled connection. Call once on shutdown."""
        while True:
            try:
                self._free.get_nowait().close()
            except queue.Empty:
                return


# One shared pool per worker process. Import this everywhere:
#     from db import pool
pool = SnowflakeConnectionPool(size=4)
