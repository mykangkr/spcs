import { Routes, Route, Link } from 'react-router-dom'
import './App.css'
import HomePage from './pages/HomePage'
import TasksPage from './pages/TasksPage'
import WizardLayout from './pages/wizard/WizardLayout'
import StepText from './pages/wizard/StepText'
import StepPriority from './pages/wizard/StepPriority'
import StepReview from './pages/wizard/StepReview'

function App() {
  return (
    <div>
      <nav style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Link to="/">Home</Link>
        <Link to="/tasks">Tasks</Link>
        <Link to="/wizard">New Task (Wizard)</Link>
      </nav>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/wizard" element={<WizardLayout />}> {/* parent: renders <Outlet /> */} 
          <Route index element={<StepText />} />          {/* child: index = the default child at /wizard/ */}  
          <Route path="step2" element={<StepPriority />} /> {/* child: rendered at /wizard/step2 */}
          <Route path="step3" element={<StepReview />} />   {/* child: rendered at /wizard/step3 */}
        </Route>
      </Routes>
    </div>
  )
}

export default App
