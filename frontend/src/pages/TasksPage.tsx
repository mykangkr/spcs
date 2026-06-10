import { useState, useEffect } from 'react'
import type { Task } from '../types'
import * as api from '../api'
import TaskList from '../components/TaskList'
import AddTaskForm from '../components/AddTaskForm'

function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])

  useEffect(() => {
    async function load() {
      const data = await api.getTasks()
      setTasks(data)
    }
    load()
  }, []) // [] = run once, on mount

  async function addTask(text: string) {
    const created = await api.createTask(text)
    setTasks([...tasks, created])
  }

  async function toggleTask(id: string) {
    const updated = await api.toggleTask(id)
    setTasks(tasks.map((t) => (t.id === id ? updated : t)))
  }

  async function deleteTask(id: string) {
    await api.deleteTask(id)
    setTasks(tasks.filter((t) => t.id !== id))
  }

  return (
    <div>
      <h1>My Tasks</h1>
      <AddTaskForm onAdd={addTask} />
      <TaskList tasks={tasks} onToggle={toggleTask} onDelete={deleteTask} />
    </div>
  )
}

export default TasksPage
