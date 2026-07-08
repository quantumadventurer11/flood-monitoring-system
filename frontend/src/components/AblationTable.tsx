import type { PaperResults } from "../api/client";

export default function AblationTable({ rows }: { rows: PaperResults["ablation_results"] }) {
  const statusBadge = (status?: string) => status === "REAL_UNOSAT_VALIDATION"
    ? <span className="rounded bg-emerald-100 px-2 py-1 text-xs font-bold text-emerald-800">REAL</span>
    : <span className="rounded bg-red-100 px-2 py-1 text-xs font-bold text-red-800">SIMULATED / NOT PUBLISHABLE</span>;

  return (
    <div>
      <table className="w-full min-w-[760px] overflow-hidden rounded-lg text-left text-sm">
        <thead className="bg-slate-900 text-white">
          <tr>{["Configuration", "Status", "Features", "ROC-AUC", "Accuracy", "Precision", "Recall", "F1", "Time(s)"].map((h) => <th key={h} className="p-3">{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.configuration} className="border-b border-slate-200 bg-white">
              <td className="p-3 font-semibold">{row.configuration}</td><td className="p-3">{statusBadge(row.result_status)}</td><td className="p-3">{row.features}</td><td className="p-3">{row.roc_auc.toFixed(4)}</td><td className="p-3">{row.accuracy.toFixed(4)}</td><td className="p-3">{row.precision.toFixed(4)}</td><td className="p-3">{row.recall.toFixed(4)}</td><td className="p-3">{row.f1.toFixed(3)}</td><td className="p-3">{row.time_s.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-sm text-slate-600">These rows are real UNOSAT label-margin ablations using the NDWI-free XGBoost model; NDWI water fraction is reported only as an audited validation score.</p>
    </div>
  );
}
