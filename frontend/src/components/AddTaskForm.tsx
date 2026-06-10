import { useState } from "react";

type AddTaskFormProps = {
  onAdd: (text: string) => void;
};

function AddTaskForm({ onAdd }: AddTaskFormProps) {
  const [text, setText] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return; // ignore empty input
    onAdd(trimmed);
    setText(""); // clear the input
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="New task"
      />
      <button type="submit">Add Task</button>
    </form>
  );
}

export default AddTaskForm;
