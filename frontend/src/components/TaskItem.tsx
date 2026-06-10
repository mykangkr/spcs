import type { Task } from "../types";

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
        {task.text}
      </span>
      <button onClick={() => onDelete(task.id)}>Delete</button>
    </li>
  );
}

export default TaskItem;