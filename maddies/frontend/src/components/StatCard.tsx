interface Props {
  label: string;
  value: string | number;
  accent?: string;
}

export default function StatCard({ label, value, accent = "bg-white" }: Props) {
  return (
    <div className={`rounded-xl border border-slate-200 p-5 shadow-sm ${accent}`}>
      <div className="text-sm font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-3xl font-bold text-slate-900">{value}</div>
    </div>
  );
}
