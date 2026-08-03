import { useEffect, useState } from "react";

import * as api from "../api";
import { useAuth } from "../auth";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import type { DashboardData } from "../types";

const TITLES: Record<string, string> = {
  organization: "CEO Dashboard — Organization Overview",
  operations: "Super Admin Dashboard — Operations",
  team: "Admin Dashboard — My Team",
  workspace: "My Workspace",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch(() => setError("Failed to load dashboard."));
  }, []);

  if (error) return <div className="text-rose-600">{error}</div>;
  if (!data || !user) return <div>Loading…</div>;

  const statEntries = Object.entries(data.stats);

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold">{TITLES[data.scope]}</h1>
      <p className="mb-6 text-sm text-slate-500">Welcome back, {user.email}</p>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
        {statEntries.map(([key, value]) => (
          <StatCard key={key} label={key.replace(/_/g, " ")} value={value} />
        ))}
      </div>

      {/* CEO / Superadmin: recent activity feed */}
      {data.recent_activity && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">Recent activity</h2>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            {data.recent_activity.length === 0 && (
              <p className="p-4 text-sm text-slate-500">No activity yet.</p>
            )}
            {data.recent_activity.map((a) => (
              <div key={a.id} className="flex items-center gap-3 border-b border-slate-100 px-4 py-3 text-sm last:border-0">
                <span className="font-medium">{a.actor_email ?? "system"}</span>
                <span className="text-slate-600">{a.detail || a.action}</span>
                <span className="ml-auto text-xs text-slate-400">
                  {new Date(a.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Superadmin: maddies by status */}
      {data.maddies_by_status && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">Maddies by status</h2>
          <div className="flex gap-3">
            {data.maddies_by_status.map((row) => (
              <div key={row.status} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3">
                <StatusBadge value={row.status} />
                <span className="text-xl font-bold">{row.count}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Admin: my maddies */}
      {data.my_maddies && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">My maddies</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {data.my_maddies.map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4">
                <div>
                  <div className="font-medium">{m.full_name}</div>
                  <div className="text-xs text-slate-500">{m.skills || "—"}</div>
                </div>
                <StatusBadge value={m.status} />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Employee: tasks + assignments */}
      {data.my_tasks && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">My open tasks</h2>
          <div className="space-y-2">
            {data.my_tasks.length === 0 && <p className="text-sm text-slate-500">All caught up!</p>}
            {data.my_tasks.map((t) => (
              <div key={t.id} className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4">
                <StatusBadge value={t.priority} />
                <span className="flex-1 font-medium">{t.title}</span>
                <StatusBadge value={t.status} />
              </div>
            ))}
          </div>
        </section>
      )}
      {data.my_assignments && data.my_assignments.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">My active assignments</h2>
          <div className="space-y-2">
            {data.my_assignments.map((a) => (
              <div key={a.id} className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
                <span className="font-medium">{a.maddie_name}</span>
                <span className="text-slate-500"> → {a.client_name}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
