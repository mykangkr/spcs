# SPCS App — Study Notes

Learning journey building a full-stack task app: **React (TypeScript) → FastAPI → SQLite**, local-first,
on the path to Snowpark Container Services (SPCS) with Snowflake + Cortex LLM later.

---

## 0. The big picture (architecture)

```
┌─────────────┐     HTTP/JSON      ┌──────────────┐     SQL      ┌──────────────┐
│  React app  │ ─────────────────> │   FastAPI    │ ──────────> │  Database    │
│  (browser)  │ <───────────────── │ (middle tier)│ <────────── │              │
└─────────────┘                    └──────────────┘             └──────────────┘
   the "front"        the "API"          the "backend"

  PHASE 1 (now):   React  ──>  FastAPI  ──>  SQLite (local file)
  PHASE 4 (later): React  ──>  FastAPI  ──>  Snowflake, inside Docker on SPCS
```

Key insight: **the React app barely changes between local and Snowflake.** It just talks to "an API."
Whether the API reads from SQLite or Snowflake is invisible to React — which is why we can learn
everything locally with no Snowflake access.

### Roadmap
| Phase | Status |
|-------|--------|
| 1. React fundamentals | ✅ done |
| 2. React ↔ FastAPI ↔ SQLite | ✅ done |
| 3. Component decomposition + routing + **wizard pages** | 🔄 in progress |
| 4. Swap SQLite → Snowflake + Cortex LLM | later (waiting on service account) |
| 5. Docker + SPCS deploy | later (waiting on proxy cert) |

### Team-mandated folder structure
```
backend/                       frontend/
  models/                        src/
  routers/                       index.html
  services/                      vite.config.ts
  main.py
```

---

## 1. Tooling & running the apps

Installed: Node v24, npm v11, Python 3.14, git. (Docker deferred — needs company proxy cert.)

### Frontend (React + Vite + TypeScript)
Scaffolded with: `npm create vite@latest frontend -- --template react-ts`

```bash
cd frontend
npm install          # one-time, on fresh checkout — downloads node_modules/
npm run dev          # start dev server → http://localhost:5173
```
- `npm run dev` runs **Vite** (the `dev` script in `package.json`).
- **Hot reload (HMR):** save a file → browser updates instantly, no refresh.
- Stop with `Ctrl+C`.

### Backend (FastAPI + uvicorn)
```bash
cd backend
python3 -m venv .venv                          # one-time: create virtual env
.venv/bin/pip install -r requirements.txt      # one-time: install deps
.venv/bin/uvicorn main:app --reload --port 8000
```
- `main:app` = "in `main.py`, the variable `app`."
- `--reload` = hot reload for Python.
- Auto-generated interactive API docs at **http://localhost:8000/docs** (Swagger UI).

> Both servers run at once: React on `:5173`, FastAPI on `:8000`. That two-process setup IS the architecture.

---

## 2. React mental model (the fundamentals)

### Single Page Application
`index.html` has one empty `<div id="root">`. `main.tsx` tells React to render `<App />` into it.
All UI is built dynamically by JavaScript inside that div.

### The four core ideas
1. **A component is a function that returns markup (JSX).**
   ```tsx
   function App() { return <h1>Hello</h1> }
   ```
2. **JSX = HTML-looking syntax inside JS.** Gotchas vs HTML:
   - `class` → `className`
   - drop JS expressions in with `{curlyBraces}`: `<p>Count is {count}</p>`
3. **State + re-rendering is the core loop.**
   ```tsx
   const [count, setCount] = useState(0)
   ```
   > Calling `setCount(...)` makes React **re-run the whole component** and update the screen.
   You never touch the DOM manually — you change *state* and describe what the UI should look like
   (declarative).
4. **Events wire user actions to state.**
   ```tsx
   onClick={() => setCount((c) => c + 1)}
   ```
   click → setter → state changes → component re-runs → screen updates.

### `useState` — where setters come from
```tsx
const [tasks, setTasks] = useState<Task[]>([])
```
- `useState(...)` **returns a 2-element array**: `[currentValue, setterFunction]`. We destructure + name them.
- **You pick the names**; convention is `x` / `setX`.
- **React owns the setter.** Calling it (1) stores the new value, (2) schedules a re-render.
- Subtlety: after `setText('hi')`, the `text` variable in the *current* render is still old — the new
  value appears on the *next* render.
- TS type: `React.Dispatch<React.SetStateAction<Task[]>>` — accepts a new value *or* a
  function `(prev) => next`.

### Lists & keys
```tsx
<ul>
  {tasks.map((task) => (
    <li key={task.id}>{task.text}</li>
  ))}
</ul>
```
- Turn arrays into elements with `.map()`.
- Each item needs a unique **`key`** so React can track items efficiently.
- `key` belongs where the list is generated (the parent's `.map()`), even when the item is a component.
- Use a stable unique id (`task.id`), not text or array index.

### Events: function reference vs wrapper
```tsx
onClick={addTask}                    // pass the function — called on click (no args)
onClick={() => deleteTask(task.id)}  // wrapper — needed when passing arguments
```
- `onClick` wants a function to call **later**.
- `onClick={deleteTask(task.id)}` (no arrow) would **call it immediately during render** and pass the
  return value — wrong, and can cause infinite render loops (it calls a setter during render).
- Wrap in `() =>` whenever you need to pass arguments.

---

## 3. Immutable updates & the spread operator

### `...` = spread operator (plain JavaScript)
"Take all items out of this array/object and drop them in here individually."
```js
[...tasks, newItem]              // new array: old items + one more
['x', ...tasks]                  // works at the front too
{ ...user, age: 31 }             // copy object, override one field
```
- `[tasks, x]` → nested array `[[...], x]` (wrong). `[...tasks, x]` → flat (right).

### Why immutability matters in React
```js
setTasks([...tasks, item])   // ✅ NEW array reference → React re-renders
tasks.push(item)             // ❌ mutates SAME array → React sees no change → no re-render
```
React detects changes by reference (`Object.is`). Always build a **new** array/object.

### The three update patterns
```tsx
// ADD: spread
setTasks([...tasks, created])

// TOGGLE/EDIT one item: map, returning a copy of the matched one
setTasks(tasks.map((t) => (t.id === id ? { ...t, done: !t.done } : t)))

// DELETE: filter
setTasks(tasks.filter((t) => t.id !== id))
```

---

## 4. TypeScript in React

### Define a shared type, use it everywhere
```ts
// src/types.ts
export type Task = {
  id: string
  text: string
  done: boolean
}
```
```tsx
const [tasks, setTasks] = useState<Task[]>([])   // <Task[]> pins the state's shape
function toggleTask(id: string) { ... }          // annotate params (no implicit any)
```
- `useState<Task[]>(...)` — the `<Task[]>` is a **generic type argument**.
- Without param types, `strict` mode errors: *"Parameter 'id' implicitly has an 'any' type."*
- Payoff: the editor autocompletes `.id`/`.text`/`.done` and catches typos.
- **Vite/esbuild does NOT type-check** — it only strips types. So TS errors won't stop the dev server;
  the red squiggles come from the editor's TS language server. Still real bugs — fix them.

### Event typing gotcha
- `React.FormEvent` / bare `FormEvent` are flagged **deprecated** in current React types.
- Clean fix: type the **handler**, not the event — lets TS infer `e`:
  ```tsx
  import { useState, type FormEventHandler } from 'react'
  const handleSubmit: FormEventHandler<HTMLFormElement> = (e) => { e.preventDefault(); ... }
  ```

---

## 5. `useEffect` & persistence

### `useEffect` — run side-effects
`useState` holds data; `useEffect` runs **side-effects** (localStorage, fetch, timers).
```tsx
useEffect(() => { /* effect */ }, [dependencies])
```
| Deps | Runs |
|------|------|
| `[tasks]` | after first render + whenever `tasks` changed |
| `[]` | **once**, on mount |
| omitted | after every render (rarely wanted) |

### localStorage persistence (Phase 1, before the backend)
- `localStorage` only stores **strings** → serialize with `JSON.stringify` / `JSON.parse`.
- **Save:** effect on `[tasks]`:
  ```tsx
  useEffect(() => { localStorage.setItem('tasks', JSON.stringify(tasks)) }, [tasks])
  ```
- **Load:** use the **lazy initializer** of `useState` (runs once, before first render):
  ```tsx
  const [tasks, setTasks] = useState<Task[]>(() => {
    const saved = localStorage.getItem('tasks')
    return saved ? JSON.parse(saved) : [/* defaults */]
  })
  ```
  > `useState(expensive())` runs every render; `useState(() => expensive())` runs once. That's the
  lazy-initializer trick. Prefer it over a load-effect to avoid an empty flash.

### Loading data from an API (after the backend exists)
The effect callback **can't be `async`** (async returns a Promise; useEffect wants nothing/cleanup).
Define an async fn inside and call it:
```tsx
useEffect(() => {
  async function load() {
    const data = await api.getTasks()
    setTasks(data)
  }
  load()
}, [])   // load once on mount
```

---

## 6. FastAPI backend (for a Flask expert)

### Flask → FastAPI Rosetta Stone
| Flask | FastAPI |
|-------|---------|
| `@app.route("/x", methods=["POST"])` | `@app.post("/x")` |
| `request.get_json()` + manual validation | typed param `body: TaskCreate` (auto-parsed & validated) |
| `jsonify(data)` | just `return data` (dict or Pydantic model) |
| `Blueprint` / `register_blueprint` | `APIRouter` / `include_router` |
| `<string:task_id>` route + arg | `{task_id}` path + `task_id: str` arg |
| `return x, 201` | `return x` + `status_code=201` in decorator |
| `abort(404)` | `raise HTTPException(status_code=404, detail=...)` |
| `flask run` | `uvicorn main:app --reload` |
| WSGI (sync) | ASGI (async-capable; sync `def` still works) |

### Layered design (matches the team folder structure)
| Layer | File | Responsibility |
|-------|------|----------------|
| **models** | `models/task.py` | data *shape* — Pydantic schemas |
| **services** | `services/task_service.py` | business logic + **all DB access** |
| **routers** | `routers/tasks.py` | HTTP endpoints — parse, call services, return |

**Rule:** routers never touch the DB directly — they call services. So the SQLite → Snowflake swap
later touches **only `services/`**.

### Models (Pydantic)
```python
class TaskCreate(BaseModel):   # INPUT shape — what the client sends
    text: str

class Task(BaseModel):         # OUTPUT shape — what's stored/returned
    id: str
    text: str
    done: bool
```
- `BaseModel` gives automatic validation (missing/wrong field → 422 before your code runs).
- Separate input vs output models: client shouldn't send `id`/`done` (server owns them).

### Services + SQLite
```python
import sqlite3, uuid
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "tasks.db"

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # access columns by name: row["text"]
    return conn

def create_task(data: TaskCreate) -> Task:
    task = Task(id=str(uuid.uuid4()), text=data.text, done=False)
    with closing(_connect()) as conn, conn:   # see gotcha below
        conn.execute("INSERT INTO tasks (id, text, done) VALUES (?, ?, ?)",
                     (task.id, task.text, int(task.done)))
    return task
```
Gotchas:
- **SQLite has no boolean** — store `done` as `0`/`1` (INTEGER), convert with `bool()`/`int()`.
  (Snowflake *does* have BOOLEAN → simpler later.)
- **Always use `?` placeholders** — never f-string SQL (injection).
- **⚠️ `with sqlite3_connection as conn:` does NOT close the connection** — it only commits/rolls back.
  Use `with closing(_connect()) as conn, conn:` — two context managers:
  1. `closing(...) as conn` → guarantees `.close()`
  2. `, conn` → the transaction (commit/rollback)
  On exit they unwind in reverse: commit, then close.

### Routers
```python
from fastapi import APIRouter, HTTPException
router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("", response_model=list[Task])
def list_all(): return task_service.list_tasks()

@router.post("", response_model=Task, status_code=201)
def create(body: TaskCreate): return task_service.create_task(body)

@router.patch("/{task_id}", response_model=Task)
def toggle(task_id: str):
    task = task_service.toggle_task(task_id)
    if task is None: raise HTTPException(404, "Task not found")
    return task

@router.delete("/{task_id}", status_code=204)
def delete(task_id: str):
    if not task_service.delete_task(task_id): raise HTTPException(404, "Task not found")
    # return nothing → 204 No Content
```
- `prefix="/tasks"` → `@router.get("")` = `GET /tasks`.
- `response_model=Task` validates/serializes the return AND documents it in Swagger.
- **204 No Content** for delete: return `None`, no body.

### Wiring in `main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import tasks
from services.task_service import init_db

app = FastAPI(title="Task API")

# CORS: let the React dev server (different origin) call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()                          # create the table at startup
app.include_router(tasks.router)
```

---

## 7. Connecting React to the API

### CORS (the browser security gate)
React (`:5173`) and FastAPI (`:8000`) are **different origins** (different port). Browsers block
cross-origin calls by default; the **server** must explicitly allow it via `CORSMiddleware` (above).

### `fetch` + `async/await` — the API module (`src/api.ts`)
Mirror of the backend services layer: keep all HTTP in one place.
```ts
import type { Task } from './types'
const BASE = 'http://localhost:8000'

export async function getTasks(): Promise<Task[]> {
  const res = await fetch(`${BASE}/tasks`)
  if (!res.ok) throw new Error(`GET /tasks failed: ${res.status}`)
  return res.json()                         // ⚠️ MUST return the parsed body
}

export async function createTask(text: string): Promise<Task> {
  const res = await fetch(`${BASE}/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error(`POST /tasks failed: ${res.status}`)
  return res.json()
}

export async function toggleTask(id: string): Promise<Task> {
  const res = await fetch(`${BASE}/tasks/${id}`, { method: 'PATCH' })
  if (!res.ok) throw new Error(`PATCH failed: ${res.status}`)
  return res.json()
}

export async function deleteTask(id: string): Promise<void> {
  const res = await fetch(`${BASE}/tasks/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`DELETE failed: ${res.status}`)
  // ⚠️ NO res.json() — 204 has no body; parsing would throw
}
```

### Async handlers — update state from the SERVER's response
```tsx
async function addTask(text: string) {
  const created = await api.createTask(text)   // server assigns the id now
  setTasks([...tasks, created])                // use the server object
}
```
- Event handlers can be `async`; React just fires them (doesn't await).
- The server owns the id → stop using `crypto.randomUUID()` on the client.

---

## 8. Components & props

### The pattern: "data down, callbacks up"
- A component is a function; **props are its parameters**.
- Data flows **down** (parent → child) via props.
- Children talk **up** by calling **callback functions** passed as props.

```tsx
// child receives data + callback props
type TaskItemProps = {
  task: Task
  onToggle: (id: string) => void
  onDelete: (id: string) => void
}
function TaskItem({ task, onToggle, onDelete }: TaskItemProps) {
  return (
    <li>
      <input type="checkbox" checked={task.done} onChange={() => onToggle(task.id)} />
      <span style={{ textDecoration: task.done ? 'line-through' : 'none' }}>{task.text}</span>
      <button onClick={() => onDelete(task.id)}>Delete</button>
    </li>
  )
}

// parent passes them down
<TaskItem key={task.id} task={task} onToggle={toggleTask} onDelete={deleteTask} />
```

### Where should state live?
- State lives in the **lowest component that needs it.**
- Only one component needs the input text → keep it local (in `AddTaskForm`).
- Two+ components need `tasks` → **lift it up** to the shared parent (the page).

### A self-contained form child
```tsx
function AddTaskForm({ onAdd }: { onAdd: (text: string) => void }) {
  const [text, setText] = useState('')
  const handleSubmit: FormEventHandler<HTMLFormElement> = (e) => {
    e.preventDefault()                     // stop default full-page reload
    const trimmed = text.trim()
    if (!trimmed) return
    onAdd(trimmed)                         // callback up
    setText('')                            // clear own input
  }
  return (
    <form onSubmit={handleSubmit}>
      <input value={text} onChange={(e) => setText(e.target.value)} />
      <button type="submit">Add Task</button>
    </form>
  )
}
```
- Using a real `<form onSubmit>` makes **Enter** submit too.
- `e.preventDefault()` stops the browser's default page reload on submit.

---

## 9. Routing (React Router)

Install: `npm install react-router-dom`

| Piece | Role |
|-------|------|
| `<BrowserRouter>` (in `main.tsx`) | turns on URL routing for the whole app |
| `<Routes>` + `<Route path element>` | the route table: URL → component |
| `<Link to="/tasks">` | navigate **without** a page reload (client-side) |
| `pages/` folder | convention: one component per route |

```tsx
// main.tsx — wrap the app
<StrictMode>
  <BrowserRouter>
    <App />
  </BrowserRouter>
</StrictMode>

// App.tsx — router shell
function App() {
  return (
    <div>
      <nav><Link to="/">Home</Link> <Link to="/tasks">Tasks</Link></nav>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/tasks" element={<TasksPage />} />
      </Routes>
    </div>
  )
}
```

### Folder structure after routing
```
src/
├── main.tsx          ← <BrowserRouter>
├── App.tsx           ← router shell (nav + <Routes>)
├── types.ts          ← shared Task type
├── api.ts            ← all HTTP calls
├── components/       ← reusable widgets (TaskItem, TaskList, AddTaskForm)
└── pages/            ← full screens per URL (HomePage, TasksPage)
```
- **components/** = reusable bits; **pages/** = full screens mapped to URLs.

### Multi-step wizard
A wizard = one flow split across steps, each its own route, with Next/Back and **data shared across steps**.

**Architecture:** a parent `WizardLayout` holds the "being-built" object and renders `<Outlet>`; each step
reads/writes it via `useOutletContext` and moves on via `useNavigate`.

| Concept | Role |
|---------|------|
| Nested routes | child routes render *inside* a parent layout route |
| `<Outlet>` | placeholder where the active child step renders |
| `<Outlet context={...}>` + `useOutletContext<T>()` | share parent state down to the steps |
| `useNavigate()` | programmatic nav: `navigate('/wizard/step2')`, `navigate(-1)` (back) |
| `index` route | the default child shown at the parent's exact path |

```tsx
// Parent: holds shared state, renders the active step
function WizardLayout() {
  const [data, setData] = useState<WizardData>({ text: '', priority: 'medium' })
  return <div><h1>New Task Wizard</h1><Outlet context={{ data, setData }} /></div>
}

// A step: read/write shared state, then navigate
const { data, setData } = useOutletContext<WizardContext>()
const navigate = useNavigate()
<button onClick={() => navigate('/wizard/step2')} disabled={!data.text.trim()}>Next →</button>

// Routes: nested, with RELATIVE child paths
<Route path="/wizard" element={<WizardLayout />}>
  <Route index element={<StepText />} />
  <Route path="step2" element={<StepPriority />} />
  <Route path="step3" element={<StepReview />} />
</Route>

// Final step: async work + redirect
async function handleCreate() {
  await api.createTask(data.text, data.priority)
  navigate('/tasks')   // TasksPage's mount effect reloads the list automatically
}
```
- **State lives in the PARENT** so it survives step changes — that's the heart of the pattern.
- `navigate(-1)` = browser back (leaves the wizard if deep-linked); `navigate('/wizard')` = always step 1.

---

## 10. Vertical slice — adding a field end-to-end (`priority`)

Adding one field touches **every layer except routers** — which is exactly the payoff of the layering
(and a preview of how the SQLite→Snowflake swap will be contained to `services/`).

| Layer | Change |
|-------|--------|
| `models/task.py` | add `priority` to `TaskCreate` (with default) and `Task` |
| `services/task_service.py` | DB column + include in SELECT/INSERT + a migration |
| `routers/tasks.py` | **nothing** — `response_model=Task` serializes the new field automatically |
| `types.ts` | add `priority` (+ a `Priority` union) to `Task` |
| `api.ts` | send `priority` in `createTask` |
| UI (`StepReview`, `TaskItem`) | set it / display it |

### Backend: a typed enum with `Literal`
```python
from typing import Literal
Priority = Literal["low", "medium", "high"]   # same validation power as the TS union

class TaskCreate(BaseModel):
    text: str
    priority: Priority = "medium"             # default if omitted
class Task(BaseModel):
    id: str; text: str; done: bool; priority: Priority
```
Send `"urgent"` → automatic **422** (no manual validation).

### Backend: SQLite migration for an existing DB
`CREATE TABLE IF NOT EXISTS` does **not** alter an existing table, so an older DB lacks the new column.
Idempotent fix inside `init_db`:
```python
existing = [r["name"] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()]
if "priority" not in existing:
    conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
```

### Frontend: exhaustive maps with `Record<Union, T>`
```tsx
const PRIORITY_COLORS: Record<Priority, string> = {
  low: '#e0e0e0', medium: '#ffe0b2', high: '#ffcdd2',
}
background: PRIORITY_COLORS[task.priority]
```
`Record<Priority, string>` forces a value for **every** union member — miss one and TS errors. Add a new
priority later and the compiler makes you handle it here. Ideal for mapping a union → colors/labels/icons.

### Keep optional defaults for backward-compat
`createTask(text, priority = 'medium')` lets the old quick-add (`createTask(text)`) keep working while the
wizard passes an explicit priority.

---

## 11. Lessons learned (gotchas we actually hit)

1. **`text-align: center` is inherited** — a rule on `#root` centered the whole app, not the `<ul>`.
2. **Helper functions must live *inside* the component** to see its `useState` variables (closure/scope).
   A function defined outside can't access `tasks`/`setTasks`.
3. **`api` functions must `return res.json()`** — forgetting it returns `undefined`. Symptom: add/toggle
   needed a manual refresh (they put `undefined` into state and crashed render), while delete worked
   (it ignores the return value). The asymmetry pointed straight at the bug.
4. **204 responses have no body** — don't call `res.json()` on a DELETE.
5. **Relative import paths are relative to the importing file** — moving code into `components/` means
   `./App` → `../App` (and we later centralized the type in `types.ts`).
6. **Confirm files actually saved** — two component files were 0 bytes (paste didn't save) → blank app
   with no obvious error. An empty import silently breaks the screen.
7. **Vite doesn't type-check** — the app can run with TypeScript errors; trust the editor's squiggles.
8. **`with sqlite3_conn` commits but doesn't close** — use `contextlib.closing`.
9. **`CREATE TABLE IF NOT EXISTS` won't migrate an existing table** — add new columns explicitly
   (`PRAGMA table_info` to check, then `ALTER TABLE ... ADD COLUMN`).
10. **Wizard state must live in the parent** (shared via `Outlet` context), not inside each step —
    otherwise it resets every time you change steps.
11. **`Record<Union, T>` gives compile-time exhaustiveness** — handle every union member or TS errors.

---

## Quick command reference

```bash
# Frontend
cd frontend && npm run dev                 # http://localhost:5173

# Backend
cd backend && .venv/bin/uvicorn main:app --reload --port 8000   # http://localhost:8000
#   API docs: http://localhost:8000/docs

# Inspect the DB quickly
curl -s http://localhost:8000/tasks
```
