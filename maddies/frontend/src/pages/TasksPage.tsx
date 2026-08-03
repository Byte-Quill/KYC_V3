import { useEffect, useState, type FormEvent } from "react";

import * as api from "../api";
import StatusBadge from "../components/StatusBadge";
import type { Task } from "../types";

const COLUMNS: { key: Task["status"]; label: string }[] = [
  { key: "todo", label: "To Do" },
  { key: "in_progress", label: "In Progress" },
  { key: "done", label: "Done" },
];

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");

  const load = () => api.listTasks().then(setTasks).catch(() => setError("Failed to load."));
  useEffect(() => { load(); }, []);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.createTask({
        title: fd.get("title") as string,
        priority: fd.get("priority") as Task["priority"],
        due_date: (fd.get("due_date") as string) || undefined,
      });
      e.currentTarget.reset();
      load();
    } catch {
      setError("Failed to create task.");
    }
  }

  async function onAdvance(id: string) {
    await api.advanceTask(id);
    load();
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Tasks</h1>
      {error && <div className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      <form onSubmit={onCreate} className="mb-6 flex flex-wrap gap-3 rounded-xl border border-slate-200 bg-white p-4">
        <input name="title" required placeholder="New task…" className="min-w-0 flex-1 rounded-lg border px-3 py-2" />
        <select name="priority" className="rounded-lg border px-3 py-2">
          <option value="low">Low</option>
          <option value="medium" selected>Medium</option>
          <option value="high">High</option>
        </select>
        <input name="due_date" type="date" className="rounded-lg border px-3 py-2" />
        <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white">Add</button>
      </form>

      <div className="grid gap-4 md:grid-cols-3">
        {COLUMNS.map((col) => (
          <div key={col.key} className="rounded-xl bg-slate-200/60 p-3">
            <div className="mb-3 flex items-center justify-between px-1">
              <span className="text-sm font-semibold">{col.label}</span>
              <span className="text-xs text-slate-500">
                {tasks.filter((t) => t.status === col.key).length}
              </span>
            </div>
            <div className="space-y-2">
              {tasks.filter((t) => t.status === col.key).map((t) => (
                <div key={t.id} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <span className="text-sm font-medium">{t.title}</span>
                    <StatusBadge value={t.priority} />
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{t.due_date ?? "No due date"}</span>
                    {t.status !== "done" && (
                      <button
                        onClick={() => onAdvance(t.id)}
                        className="rounded bg-indigo-50 px-2 py-1 font-semibold text-indigo-700 hover:bg-indigo-100"
                      >
                        Advance →
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
