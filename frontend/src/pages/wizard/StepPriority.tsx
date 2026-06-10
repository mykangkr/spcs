import { useOutletContext, useNavigate } from 'react-router-dom'
import type { WizardContext } from './WizardLayout'
import type { Priority } from '../../types'


function StepPriority() {
    const { data, setData } = useOutletContext<WizardContext>() // read parent's shared state
    const navigate = useNavigate()                      // get the navigate function to programmatically change routes

    return (
        <div>
            <h2>Step 2 of 3 — Priority</h2>
            <label>
                How important is this task?{' '}
                <select
                    value={data.priority}                           // contolled by the shared state
                    onChange={(e) => setData({ ...data, priority: e.target.value as Priority })}  // write back immutably to the shared state
                >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                </select>
            </label>

            <div style={{ marginTop: 12 }}>
                <button onClick={() => navigate('/wizardI ')}>← Back</button>
                <button onClick={() => navigate('/wizard/step3')}>Next →</button>
            </div>
        </div>
    )   
}

export default StepPriority