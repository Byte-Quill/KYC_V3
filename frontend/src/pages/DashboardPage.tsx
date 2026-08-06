import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import * as api from "../api";
import StatusBadge from "../components/StatusBadge";
import type { KYCApplication } from "../types";

export default function DashboardPage() {
  const [applications, setApplications] = useState<KYCApplication[]>([]);
  const [count, setCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const [pageNum, setPageNum] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async (pageNumber: number) => {
    setLoading(true);
    setError("");
    try {
      const data = await api.listApplications(pageNumber);
      setApplications(data.results);
      setCount(data.count);
      setHasNext(!!data.next);
      setHasPrev(!!data.previous);
    } catch {
      setError("Failed to load applications.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(pageNum);
  }, [load, pageNum]);

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

      <div className="mt-6 flex items-center justify-between text-sm">
        <span className="text-slate-500">{count} total</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPageNum((n) => Math.max(1, n - 1))}
            disabled={!hasPrev || loading}
            className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-50 disabled:opacity-50"
          >
            ← Prev
          </button>
          <span className="px-2 py-1 text-slate-600">Page {pageNum}</span>
          <button
            onClick={() => setPageNum((n) => n + 1)}
            disabled={!hasNext || loading}
            className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-50 disabled:opacity-50"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
