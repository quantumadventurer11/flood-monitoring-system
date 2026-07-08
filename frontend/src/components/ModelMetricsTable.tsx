import type { PaperResults } from "../api/client";

const badges = ["bg-yellow-400 text-yellow-950", "bg-slate-300 text-slate-900", "bg-amber-700 text-white"];

export default function ModelMetricsTable({ rows }: { rows: PaperResults["model_metrics"] }) {
  const statusBadge = (status?: string) => status === "REAL_UNOSAT_VALIDATION"
    ? <span className="rounded bg-emerald-100 px-2 py-1 text-xs font-bold text-emerald-800">REAL</span>
    : <span className="rounded bg-red-100 px-2 py-1 text-xs font-bold text-red-800">SIMULATED / NOT PUBLISHABLE</span>;

  return (
    <table className="w-full min-w-[720px] overflow-hidden rounded-lg text-left text-sm">
      <thead className="bg-slate-900 text-white">
        <tr>{["Rank", "Model", "Status", "ROC-AUC", "Accuracy", "Precision", "Recall", "F1"].map((h) => <th key={h} className="p-3">{h}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.model} className={`border-b border-slate-200 ${row.rank === 1 ? "bg-yellow-50" : row.rank % 2 ? "bg-white" : "bg-slate-50"}`}>
            <td className="p-3"><span className={`rounded px-2 py-1 text-xs font-bold ${badges[row.rank - 1] ?? "bg-slate-100"}`}>{row.rank}</span></td>
            <td className="p-3 font-semibold">{row.model}</td>
            <td className="p-3">{statusBadge(row.result_status)}</td>
            <td className="p-3">{row.roc_auc.toFixed(4)}</td><td className="p-3">{row.accuracy}</td><td className="p-3">{row.precision}</td><td className="p-3">{row.recall}</td><td className="p-3">{row.f1.toFixed(3)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
