from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import tasks
from services.task_service import init_db

app = FastAPI(title="Task API")

# Allow the React dev server (different origin) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()  # Ensure the database and table are created at startup
app.include_router(tasks.router)

@app.get("/health")
def health():
    return {"status": "ok"}
