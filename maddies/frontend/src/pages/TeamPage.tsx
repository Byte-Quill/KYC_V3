import { useEffect, useState, type FormEvent } from "react";

import * as api from "../api";
import { useAuth } from "../auth";
import type { Role, User } from "../types";

const ROLE_LABELS: Record<Role, string> = {
  ceo: "CEO",
  superadmin: "Super Admin",
  admin: "Admin",
  employee: "Employee",
};

// Which roles each role may create.
const CREATABLE: Record<Role, Role[]> = {
  ceo: ["superadmin", "admin", "employee"],
  superadmin: ["admin", "employee"],
  admin: ["employee"],
  employee: [],
};

export default function TeamPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const load = () => api.listUsers().then(setUsers).catch(() => setError("Failed to load."));
  useEffect(() => { load(); }, []);

  if (!user) return null;
  const creatable = CREATABLE[user.role] ?? [];

  async function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    try {
      await api.createUser({
        email: fd.get("email") as string,
        username: fd.get("username") as string,
        password: fd.get("password") as string,
        role: fd.get("role") as Role,
      });
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof api.ApiError ? JSON.stringify(err.data) : "Failed to create user.");
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Team</h1>
        {creatable.length > 0 && (
          <button
            onClick={() => setShowForm((s) => !s)}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            {showForm ? "Cancel" : "+ Add member"}
          </button>
        )}
      </div>
      {error && <div className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {showForm && (
        <form onSubmit={onCreate} className="mb-6 grid gap-3 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-2">
          <input name="email" type="email" required placeholder="Email" className="rounded-lg border px-3 py-2" />
          <input name="username" required placeholder="Username" className="rounded-lg border px-3 py-2" />
          <input name="password" type="password" required minLength={8} placeholder="Password (min 8 chars)" className="rounded-lg border px-3 py-2" />
          <select name="role" className="rounded-lg border px-3 py-2">
            {creatable.map((r) => (
              <option key={r} value={r}>{ROLE_LABELS[r]}</option>
            ))}
          </select>
          <button className="rounded-lg bg-indigo-600 py-2 font-semibold text-white md:col-span-2">Create member</button>
        </form>
      )}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Reports to</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-medium">{u.email}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700">
                    {ROLE_LABELS[u.role]}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{u.manager_email ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
