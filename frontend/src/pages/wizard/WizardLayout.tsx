import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import type { Priority } from '../../types'

// The "task being built" as it accumulates across the wizard steps.
export type WizardData = {
  text: string
  priority: Priority
}

// The shape shared with each step via <Outlet context={...}>.
export type WizardContext = {
  data: WizardData
  setData: React.Dispatch<React.SetStateAction<WizardData>>
}

function WizardLayout() {
  // This state lives in the PARENT, so it survives as the user moves between steps.
  const [data, setData] = useState<WizardData>({ text: '', priority: 'medium' })

  return (
    <div>
      <h1>New Task Wizard</h1>
      {/* The active child step renders here, and receives `data`/`setData`. */}
      <Outlet context={{ data, setData }} />
    </div>
  )
}

export default WizardLayout
