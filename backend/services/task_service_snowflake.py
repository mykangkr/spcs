"""Snowflake version of task_service — a migration SKETCH.

This mirrors services/task_service.py (SQLite) but talks to Snowflake through
the shared connection pool. Keep the SQLite file as-is until you're ready to
swap; when you are, point routers/tasks.py at this module (or rename this over
task_service.py).

What changed vs. SQLite, and why
--------------------------------
1. Connections come from the pool, not sqlite3.connect:
       with pool.connection() as conn:   # borrow + auto-return
   No per-call file open; see SSO_connection_pooling.md.

2. Parameter style is %s (pyformat), not ? — that's the connector default.
   (You can switch the whole connector to qmark with paramstyle="qmark".)

3. Types map to native Snowflake types:
       id        TEXT    -> VARCHAR
       text      TEXT    -> VARCHAR
       done      INTEGER -> BOOLEAN   (Snowflake has a real boolean; no 0/1)
       priority  TEXT    -> VARCHAR
   So we no longer int()/bool() the done column by hand.

4. Identifiers come back UPPERCASE. With DictCursor the keys are "ID", "TEXT",
   "DONE", "PRIORITY" — note the casing when mapping rows to the model.

5. Autocommit: the connector autocommits by default, so there's no explicit
   `conn.commit()` like SQLite's `with conn:` block. DDL is committed too.

6. Schema migration: Snowflake supports ADD COLUMN IF NOT EXISTS, so the
   PRAGMA-based "does priority exist?" dance in the SQLite version isn't needed.
"""
import uuid

from snowflake.connector import DictCursor

from db import pool
from models.task import Task, TaskCreate


def _row_to_task(r: dict) -> Task:
    """Map an UPPERCASE DictCursor row to our Task model."""
    return Task(
        id=r["ID"],
        text=r["TEXT"],
        done=bool(r["DONE"]),       # already a Python bool from BOOLEAN, bool() is belt-and-suspenders
        priority=r["PRIORITY"],
    )


def init_db():
    """Create the tasks table if it doesn't exist. Called once per worker at startup."""
    with pool.connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id        VARCHAR PRIMARY KEY,
                text      VARCHAR NOT NULL,
                done      BOOLEAN NOT NULL DEFAULT FALSE,
                priority  VARCHAR NOT NULL DEFAULT 'medium'
            )
        """)
        # Idempotent column add — replaces the SQLite PRAGMA check.
        cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority VARCHAR NOT NULL DEFAULT 'medium'")


def list_tasks() -> list[Task]:
    """Return all tasks."""
    with pool.connection() as conn:
        cur = conn.cursor(DictCursor)
        cur.execute("SELECT id, text, done, priority FROM tasks")
        return [_row_to_task(r) for r in cur.fetchall()]


def create_task(data: TaskCreate) -> Task:
    """Insert a new task and return it."""
    task = Task(id=str(uuid.uuid4()), text=data.text, done=False, priority=data.priority)
    with pool.connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (id, text, done, priority) VALUES (%s, %s, %s, %s)",
            (task.id, task.text, task.done, task.priority),   # done is a real bool now
        )
    return task


def toggle_task(task_id: str) -> Task | None:
    """Flip a task's done flag. Return the updated task, or None if not found."""
    with pool.connection() as conn:
        cur = conn.cursor(DictCursor)
        cur.execute("SELECT id, text, done, priority FROM tasks WHERE id = %s", (task_id,))
        row = cur.fetchone()
        if row is None:
            return None
        new_done = not bool(row["DONE"])
        cur.execute("UPDATE tasks SET done = %s WHERE id = %s", (new_done, task_id))
        return Task(id=row["ID"], text=row["TEXT"], done=new_done, priority=row["PRIORITY"])


def delete_task(task_id: str) -> bool:
    """Delete a task. Return True if a row was removed."""
    with pool.connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        return cur.rowcount > 0
