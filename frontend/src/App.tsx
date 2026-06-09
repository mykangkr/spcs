import { useState, useEffect } from 'react'
import './App.css'

function App() {
  type Task = {
    id: string
    text: string
    done: boolean
  }

  // const [tasks, setTasks] = useState<Task[]>([
  //   { id: '1', text: 'Learn JSX', done: false },
  //   { id: '2', text: 'Learn useState', done: false },
  // ])
  const [tasks, setTasks] = useState<Task[]>(() => {
    const saved = localStorage.getItem('tasks')
    return saved ? JSON.parse(saved) : [
      { id: '1', text: 'Learn JSX', done: false },
      { id: '2', text: 'Learn useState', done: false },
    ]
  })
  const [text, setText] = useState('')

  useEffect(() => {
    localStorage.setItem('tasks', JSON.stringify(tasks))
  }, [tasks])

  function addTask() {
    setTasks([...tasks, { id: crypto.randomUUID(), text, done: false }])  // new array = old items + the new one
    setText('')                 // clear the input
  } 

  function toggleTask(id: string) {
    setTasks(tasks.map((t) =>
      t.id === id ? { ...t, done: !t.done } : t
    ))
  } 

  function deleteTask(id: string) {
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
