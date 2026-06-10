import { useOutletContext, useNavigate } from "react-router-dom";
import type { WizardContext } from "./WizardLayout";
import * as api from "../../api";

function StepReview() {
    const { data } = useOutletContext<WizardContext>(); // read parent's shared state
    const navigate = useNavigate();                      // get the navigate function to programmatically change routes

    const handleCreate = async () => {
        // Backend currently stores only `text`, so we fold the priority into it for now.
        await api.createTask(data.text, data.priority); // submit the data to the server
        navigate("/tasks"); // navigate to the list once created
    }

    return (
        <div>
            <h2>Step 3 of 3 — Review</h2>
            <p><strong>Task:</strong> {data.text}</p>
            <p><strong>Priority:</strong> {data.priority}</p>

            <div style={{ marginTop: 12 }}>
                <button onClick={() => navigate('/wizard/step2')}>← Back</button>
                <button onClick={handleCreate}>Create Task</button>
            </div>
        </div>
    )   
}

export default StepReview   