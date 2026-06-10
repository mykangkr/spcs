import { useOutletContext, useNavigate } from 'react-router-dom'
import type { WizardContext } from './WizardLayout'

function StepText() {
  // Read the shared state the parent (WizardLayout) holds.
  const { data, setData } = useOutletContext<WizardContext>() // read parent's shared state
  const navigate = useNavigate()                      // get the navigate function to programmatically change routes

  return (
    <div>
      <h2>Step 1 of 3 — Task</h2>
      <label>
        What needs doing?{' '}
        <input
          value={data.text}                           // contolled by the shared state
          onChange={(e) => setData({ ...data, text: e.target.value })}  // write back immutably to the shared state
          autoFocus
        />
      </label>

      <div style={{ marginTop: 12 }}>
        <button
          onClick={() => navigate('/wizard/step2')}                   // programmatically navigate to the next step
          disabled={!data.text.trim()}
        >
          Next →
        </button>
      </div>
    </div>
  )
}

export default StepText
