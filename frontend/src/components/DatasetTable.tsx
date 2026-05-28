import type { PaperResults } from "../api/client";

export default function DatasetTable({ rows }: { rows: PaperResults["dataset_stats"] }) {
  return (
    <div>
      <table className="w-full overflow-hidden rounded-lg text-left text-sm">
        <thead className="bg-slate-900 text-white">
          <tr><th className="p-3">Month</th><th className="p-3">Total Patches</th><th className="p-3">Flooded (%)</th></tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.month} className="border-b border-slate-200 odd:bg-white even:bg-slate-50">
              <td className="p-3 font-medium">{row.month}</td><td className="p-3">{row.total_patches.toLocaleString()}</td><td className="p-3">{row.flooded_percent}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-sm text-slate-600">Test set = August only. Threshold: &gt;5% pixels with NDWI &gt; 0.0</p>
    </div>
  );
}
