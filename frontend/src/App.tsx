import { Routes, Route, Link } from 'react-router-dom'
import './App.css'
import HomePage from './pages/HomePage'
import TasksPage from './pages/TasksPage'

function App() {
  return (
    <div>
      <nav style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Link to="/">Home</Link>
        <Link to="/tasks">Tasks</Link>
      </nav>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/tasks" element={<TasksPage />} />
      </Routes>
    </div>
  )
}

export default App
