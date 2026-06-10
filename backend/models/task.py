from pydantic import BaseModel

class TaskCreate(BaseModel):
    """What the client sends when creating a task (no id yet)."""
    text: str

class Task(BaseModel):
    """A full task as stored/returned (server assigns id and done)."""
    id: str
    text: str
    done: bool