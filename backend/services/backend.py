"""Single source of truth for which task backend is active.

Set TASK_BACKEND=snowflake to use the pooled Snowflake service; anything else
(default) uses SQLite. Importing the Snowflake module pulls in
snowflake-connector-python, so that import only happens when selected.

Everyone else imports the chosen module from here:

    from services.backend import service
    service.list_tasks()
"""
import os

if os.environ.get("TASK_BACKEND", "sqlite").lower() == "snowflake":
    from services import task_service_snowflake as service
else:
    from services import task_service as service

__all__ = ["service"]
