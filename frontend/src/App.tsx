import { useState, useEffect } from 'react'
import './App.css'
import * as api from './api'

export type Task = {
  id: string
  text: string
  done: boolean
}

function App() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [text, setText] = useState('')

  useEffect(() => {
    async function load() {
      const data = await api.getTasks()
      setTasks(data)
    }
    load()
  }, [])   // [] = run once, on mount

  async function addTask() {
    const created = await api.createTask(text)
    setTasks([...tasks, created])
    setText('')                 // clear the input
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
    <>
      <section id="center">
        <div>
          <h1>My Tasks</h1>

          <ul>
            {tasks.map((task) => (
              <li key={task.id}>
                <input type="checkbox" checked={task.done} onChange={() => toggleTask(task.id)} />
                <span style={{ textDecoration: task.done ? 'line-through' : 'none' }}>
                  {task.text}
                </span>
                <button onClick={() => deleteTask(task.id)}>Delete</button>
              </li>
            ))}
          </ul>
          <p>
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
          </p>
        </div>
        <button
          type="button"
          onClick={addTask}
        > 
          Add Task
        </button>
      </section>
    </>
  )
}


export default App
