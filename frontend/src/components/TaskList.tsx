import type { Task } from "../types";
import TaskItem from "./TaskItem";

type TaskListProps = {
  tasks: Task[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
};

function TaskList({ tasks, onToggle, onDelete }: TaskListProps) {
  return (
    <ul>
      {tasks.map((task) => (
        <TaskItem
          key={task.id}
          task={task}
          onToggle={onToggle}
          onDelete={onDelete}
        />
      ))}
    </ul>
  );
}

export default TaskList;