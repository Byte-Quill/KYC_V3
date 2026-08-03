const COLORS: Record<string, string> = {
  available: "bg-emerald-100 text-emerald-800",
  assigned: "bg-blue-100 text-blue-800",
  on_leave: "bg-amber-100 text-amber-800",
  inactive: "bg-slate-200 text-slate-600",
  active: "bg-blue-100 text-blue-800",
  completed: "bg-emerald-100 text-emerald-800",
  cancelled: "bg-rose-100 text-rose-800",
  todo: "bg-slate-200 text-slate-700",
  in_progress: "bg-amber-100 text-amber-800",
  done: "bg-emerald-100 text-emerald-800",
  low: "bg-slate-200 text-slate-600",
  medium: "bg-amber-100 text-amber-800",
  high: "bg-rose-100 text-rose-800",
};

export default function StatusBadge({ value }: { value: string }) {
  const color = COLORS[value] ?? "bg-slate-200 text-slate-700";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${color}`}>
      {value.replace(/_/g, " ")}
    </span>
  );
}
