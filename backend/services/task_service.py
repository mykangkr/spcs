import sqlite3
import uuid
from pathlib import Path

from models.task import Task, TaskCreate
from contextlib import closing

DB_PATH = Path(__file__).parent.parent / "tasks.db"

def _connect() -> sqlite3.Connection:
    """Connect to the database, creating it if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name: row["text"]
    return conn

def init_db():
    """Create the tasks table if it doesn't exist. Called once at startup."""
    with closing(_connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,    
                priority TEXT NOT NULL DEFAULT 'medium'
            )
        """)
        existing = [row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        if "priority" not in existing:
            conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")

def list_tasks() -> list[Task]:
    """Return all tasks in the database."""
    with closing(_connect()) as conn, conn:
        rows = conn.execute("SELECT id, text, done, priority FROM tasks").fetchall()
        return [Task(id=r["id"], text=r["text"], done=bool(r["done"]), priority=r["priority"]) for r in rows]

def create_task(data: TaskCreate) -> Task:
    """Create a new task in the database and return it."""
    task = Task(id=str(uuid.uuid4()), text=data.text, done=False, priority=data.priority)
    with closing(_connect()) as conn, conn:
        conn.execute(
            "INSERT INTO tasks (id, text, done, priority) VALUES (?, ?, ?, ?)",
            (task.id, task.text, int(task.done), task.priority),
        )
    return task

def toggle_task(task_id: str) -> Task | None:
    """Toggle the done status of a task for the given id. Return the updated task or None if not found."""
    with closing(_connect()) as conn, conn:
        row = conn.execute("SELECT id, text, done, priority FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        new_done = not bool(row["done"])
        conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (int(new_done), task_id))
        return Task(id=row["id"], text=row["text"], done=new_done, priority=row["priority"])

def delete_task(task_id: str) -> bool:
    """Delete the task with the given id. Return True if deleted, False if not found."""
    with closing(_connect()) as conn, conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0
