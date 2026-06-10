import type { Task } from "./types"

const BASE = "http://localhost:8000"                 // wait to parse the JSON body

export async function getTasks(): Promise<Task[]> {
    const res = await fetch(`${BASE}/tasks`)
    if (!res.ok) {
        throw new Error(`GET /tasks failed: ${res.status} ${res.statusText}`)
    }
    return res.json()
}

export async function createTask(text: string): Promise<Task> {
    const res = await fetch(`${BASE}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    })
    if (!res.ok) {
        throw new Error(`POST /tasks failed: ${res.status} ${res.statusText}`)
    }
    return res.json()
}

export async function toggleTask(id: string): Promise<Task> {
    const res = await fetch(`${BASE}/tasks/${id}`, { method: 'PATCH' })
    if (!res.ok) {
        throw new Error(`PATCH /tasks/${id} failed: ${res.status} ${res.statusText}`)
    }
    return res.json()
}

export async function deleteTask(id: string): Promise<void> {
    const res = await fetch(`${BASE}/tasks/${id}`, { method: 'DELETE' })
    if (!res.ok) {
        throw new Error(`DELETE /tasks/${id} failed: ${res.status} ${res.statusText}`)
    }
}   