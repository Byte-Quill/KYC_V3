import { useEffect, useState, type FormEvent } from "react";

import * as api from "../api";
import { useAuth } from "../auth";
import StatusBadge from "../components/StatusBadge";
import type { Maddie } from "../types";

export default function MaddiesPage() {
  const { user } = useAuth();
  const [maddies, setMaddies] = useState<Maddie[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const canManage = user && ["ceo", "superadmin", "admin"].includes(user.role);

  const load = () => api.listMaddies().then(setMaddies).catch(() => setError("Failed to load."));
  useEffect(() => { load(); }, []);

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.createMaddie({
        full_name: fd.get("full_name") as string,
        phone: fd.get("phone") as string,
        skills: fd.get("skills") as string,
        hourly_rate: fd.get("hourly_rate") as string,
      });
      setShowForm(false);
      load();
    } catch {
      setError("Failed to create maddie.");
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Maddies</h1>
        {canManage && (
          <button
            onClick={() => setShowForm((s) => !s)}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            {showForm ? "Cancel" : "+ Add maddie"}
          </button>
        )}
      </div>
      {error && <div className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {showForm && (
        <form onSubmit={onCreate} className="mb-6 grid gap-3 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-2">
          <input name="full_name" required placeholder="Full name" className="rounded-lg border px-3 py-2" />
          <input name="phone" placeholder="Phone" className="rounded-lg border px-3 py-2" />
          <input name="skills" placeholder="Skills (comma separated)" className="rounded-lg border px-3 py-2" />
          <input name="hourly_rate" type="number" step="0.01" placeholder="Hourly rate" className="rounded-lg border px-3 py-2" />
          <button className="rounded-lg bg-indigo-600 py-2 font-semibold text-white md:col-span-2">Create</button>
        </form>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Skills</th>
              <th className="px-4 py-3">Rate/hr</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Managed by</th>
            </tr>
          </thead>
          <tbody>
            {maddies.map((m) => (
              <tr key={m.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium">{m.full_name}</td>
                <td className="px-4 py-3 text-slate-600">{m.skills || "—"}</td>
                <td className="px-4 py-3">₹{m.hourly_rate}</td>
                <td className="px-4 py-3"><StatusBadge value={m.status} /></td>
                <td className="px-4 py-3 text-slate-600">{m.managed_by_email ?? "—"}</td>
              </tr>
            ))}
            {maddies.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">No maddies yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
