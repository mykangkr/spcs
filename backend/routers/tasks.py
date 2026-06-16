from fastapi import APIRouter, HTTPException

from models.task import Task, TaskCreate
from services.backend import service as task_service  # SQLite or Snowflake, per TASK_BACKEND

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("", response_model=list[Task])
def list_tasks():
    """Get all tasks."""
    return task_service.list_tasks()

@router.post("", response_model=Task, status_code=201)
def create_task(body: TaskCreate):
    """Create a new task."""
    return task_service.create_task(body)

@router.patch("/{task_id}", response_model=Task)
def toggle(task_id: str):
    """Toggle the done status of a task."""
    task = task_service.toggle_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", status_code=204)
def delete(task_id: str):
    """Delete a task."""
    if not task_service.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
        