import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import * as api from "../api";
import StatusBadge from "../components/StatusBadge";
import type { KYCApplication } from "../types";

export default function ReviewQueuePage() {
  const [queue, setQueue] = useState<KYCApplication[]>([]);
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
      const data = await api.fetchReviewQueue(pageNumber);
      setQueue(data.results);
      setCount(data.count);
      setHasNext(!!data.next);
      setHasPrev(!!data.previous);
    } catch {
      setError("Failed to load review queue.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(pageNum);
  }, [load, pageNum]);

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Review Queue</h1>
      {loading && <p className="text-slate-500">Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && queue.length === 0 && (
        <div className="rounded-lg bg-white p-10 text-center shadow">
          <p className="text-slate-600">No applications awaiting review. 🎉</p>
        </div>
      )}

      <div className="overflow-hidden rounded-lg bg-white shadow">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Applicant</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">ID</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Docs</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Submitted</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Status</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {queue.map((app) => (
              <tr key={app.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <p className="font-medium">{app.full_name}</p>
                  <p className="text-slate-500">{app.applicant_email}</p>
                </td>
                <td className="px-4 py-3 capitalize">
                  {app.id_type.replace("_", " ")} · {app.id_number}
                </td>
                <td className="px-4 py-3">{app.documents.length}</td>
                <td className="px-4 py-3">
                  {app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : "—"}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={app.status} />
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    to={`/review/${app.id}`}
                    className="rounded bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
                  >
                    Review
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6 flex items-center justify-between text-sm">
        <span className="text-slate-500">{count} awaiting review</span>
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
