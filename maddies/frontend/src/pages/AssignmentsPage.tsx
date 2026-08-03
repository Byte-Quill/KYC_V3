import { useEffect, useState, type FormEvent } from "react";

import * as api from "../api";
import { useAuth } from "../auth";
import StatusBadge from "../components/StatusBadge";
import type { Assignment, Maddie, User } from "../types";

export default function AssignmentsPage() {
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [maddies, setMaddies] = useState<Maddie[]>([]);
  const [employees, setEmployees] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const canManage = user && ["ceo", "superadmin", "admin"].includes(user.role);

  const load = () => {
    api.listAssignments().then(setAssignments).catch(() => setError("Failed to load."));
  };
  useEffect(() => {
    load();
    api.listMaddies().then(setMaddies).catch(() => {});
    if (canManage) api.listUsers().then(setEmployees).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.createAssignment({
        maddie: fd.get("maddie") as string,
        client_name: fd.get("client_name") as string,
        client_address: fd.get("client_address") as string,
        start_date: fd.get("start_date") as string,
        assigned_to: (fd.get("assigned_to") as string) || undefined,
      });
      setShowForm(false);
      load();
    } catch {
      setError("Failed to create assignment.");
    }
  }

  async function onComplete(id: string) {
    await api.completeAssignment(id);
    load();
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Assignments</h1>
        {canManage && (
          <button
            onClick={() => setShowForm((s) => !s)}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            {showForm ? "Cancel" : "+ New assignment"}
          </button>
        )}
      </div>
      {error && <div className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {showForm && (
        <form onSubmit={onCreate} className="mb-6 grid gap-3 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-2">
          <select name="maddie" required className="rounded-lg border px-3 py-2">
            <option value="">Select maddie…</option>
            {maddies.filter((m) => m.status === "available").map((m) => (
              <option key={m.id} value={m.id}>{m.full_name}</option>
            ))}
          </select>
          <select name="assigned_to" className="rounded-lg border px-3 py-2">
            <option value="">Assign to employee…</option>
            {employees.filter((u) => u.role === "employee").map((u) => (
              <option key={u.id} value={u.id}>{u.email}</option>
            ))}
          </select>
          <input name="client_name" required placeholder="Client name" className="rounded-lg border px-3 py-2" />
          <input name="client_address" placeholder="Client address" className="rounded-lg border px-3 py-2" />
          <label className="text-sm text-slate-600">Start date
            <input name="start_date" type="date" required className="mt-1 w-full rounded-lg border px-3 py-2" />
          </label>
          <button className="self-end rounded-lg bg-indigo-600 py-2 font-semibold text-white">Create</button>
        </form>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Maddie</th>
              <th className="px-4 py-3">Client</th>
              <th className="px-4 py-3">Start</th>
              <th className="px-4 py-3">Owner</th>
              <th className="px-4 py-3">Status</th>
              {canManage && <th className="px-4 py-3"></th>}
            </tr>
          </thead>
          <tbody>
            {assignments.map((a) => (
              <tr key={a.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium">{a.maddie_name}</td>
                <td className="px-4 py-3">{a.client_name}</td>
                <td className="px-4 py-3 text-slate-600">{a.start_date}</td>
                <td className="px-4 py-3 text-slate-600">{a.assigned_to_email ?? "—"}</td>
                <td className="px-4 py-3"><StatusBadge value={a.status} /></td>
                {canManage && (
                  <td className="px-4 py-3 text-right">
                    {a.status === "active" && (
                      <button
                        onClick={() => onComplete(a.id)}
                        className="rounded-lg bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 hover:bg-emerald-100"
                      >
                        Complete
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
            {assignments.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No assignments yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
