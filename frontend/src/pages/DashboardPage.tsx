import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import * as api from "../api";
import StatusBadge from "../components/StatusBadge";
import type { KYCApplication } from "../types";

export default function DashboardPage() {
  const [applications, setApplications] = useState<KYCApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .listApplications()
      .then(setApplications)
      .catch(() => setError("Failed to load applications."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">My Applications</h1>
        <Link
          to="/applications/new"
          className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
        >
          New Application
        </Link>
      </div>

      {loading && <p className="text-slate-500">Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && applications.length === 0 && (
        <div className="rounded-lg bg-white p-10 text-center shadow">
          <p className="text-slate-600">You have no KYC applications yet.</p>
          <Link to="/applications/new" className="mt-2 inline-block font-medium text-blue-600 hover:underline">
            Start your first application →
          </Link>
        </div>
      )}

      <div className="space-y-3">
        {applications.map((app) => (
          <Link
            key={app.id}
            to={`/applications/${app.id}`}
            className="flex items-center justify-between rounded-lg bg-white p-4 shadow transition hover:shadow-md"
          >
            <div>
              <p className="font-semibold">{app.full_name}</p>
              <p className="text-sm text-slate-500">
                {app.id_type.replace("_", " ")} · {app.id_number} · created{" "}
                {new Date(app.created_at).toLocaleDateString()}
              </p>
            </div>
            <StatusBadge status={app.status} />
          </Link>
        ))}
      </div>
    </div>
  );
}
