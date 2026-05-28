import type { PaperResults } from "../api/client";

export default function AblationTable({ rows }: { rows: PaperResults["ablation_results"] }) {
  return (
    <div>
      <table className="w-full min-w-[760px] overflow-hidden rounded-lg text-left text-sm">
        <thead className="bg-slate-900 text-white">
          <tr>{["Configuration", "Features", "ROC-AUC", "Accuracy", "Precision", "Recall", "F1", "Time(s)"].map((h) => <th key={h} className="p-3">{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.configuration} className={`border-b border-slate-200 ${row.configuration === "FULL" ? "bg-green-50" : "bg-white"}`}>
              <td className="p-3 font-semibold">{row.configuration}</td><td className="p-3">{row.features}</td><td className="p-3">{row.roc_auc.toFixed(4)}</td><td className="p-3">{row.accuracy.toFixed(4)}</td><td className="p-3">{row.precision.toFixed(4)}</td><td className="p-3">{row.recall.toFixed(4)}</td><td className="p-3">{row.f1.toFixed(3)}</td><td className="p-3">{row.time_s.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-sm text-slate-600">Water fraction is intentionally surfaced as a leakage concern because it directly encodes the NDWI threshold used for labels.</p>
    </div>
  );
}
