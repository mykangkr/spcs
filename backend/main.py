from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import tasks
from services.backend import service  # SQLite or Snowflake, per TASK_BACKEND


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once per worker process. Startup goes before `yield`,
    # shutdown after. Close pooled Snowflake connections cleanly on exit.
    # Imported lazily so the app still boots before snowflake-connector-python
    # is installed / before we migrate off SQLite. Move this to a top-level
    # import once Snowflake is the real backend.
    yield
    from db import pool
    pool.close_all()


app = FastAPI(title="Task API", lifespan=lifespan)

# Allow the React dev server (different origin) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

service.init_db()  # Ensure the database and table are created at startup
app.include_router(tasks.router)

@app.get("/health")
def health():
    return {"status": "ok"}
