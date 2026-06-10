export type Priority = 'low' | 'medium' | 'high'

export type Task = {
  id: string
  text: string
  done: boolean
  priority: Priority
}
