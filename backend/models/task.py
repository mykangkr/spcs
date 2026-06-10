from pydantic import BaseModel
from typing import Literal

Priority = Literal["low", "medium", "high"]

class TaskCreate(BaseModel):
    """What the client sends when creating a task (no id yet)."""
    text: str
    priority: Priority = "medium"  # Default priority is medium

class Task(BaseModel):
    """A full task as stored/returned (server assigns id and done)."""
    id: str
    text: str
    priority: Priority
    done: bool  