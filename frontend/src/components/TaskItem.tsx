import type { Task, Priority } from "../types";

const PRIORITY_COLORS: Record<Priority, string> = {
  low: '#e0e0e0',     // grey
  medium: '#ffe0b2',  // amber
  high: '#ffcdd2',    // red-ish
};

type TaskItemProps = {
  task: Task;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
};

function TaskItem({ task, onToggle, onDelete }: TaskItemProps) {
  return (
    <li>
      <input type="checkbox" checked={task.done} onChange={() => onToggle(task.id)} />
      <span style={{ textDecoration: task.done ? 'line-through' : 'none' }}>
        <span style={{
          fontSize: 12,
          padding: '1px 6px',
          borderRadius: 4,
          marginRight: 6,
          background: PRIORITY_COLORS[task.priority],
        }}>
          {task.priority}
        </span>
        {task.text}
      </span>
      <button onClick={() => onDelete(task.id)}>Delete</button>
    </li>
  );
}

export default TaskItem;