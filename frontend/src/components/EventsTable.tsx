export default function EventsTable({ rows }: { rows: any[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          <tr><th className="p-2">Date</th><th className="p-2">Country</th><th className="p-2">Risk</th><th className="p-2">Probability</th></tr>
        </thead>
        <tbody className="text-slate-700 dark:text-slate-300">
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-slate-100 dark:border-slate-800">
              <td className="p-2">{row.event_date}</td><td className="p-2">{row.country}</td><td className="p-2">{row.risk_level}</td><td className="p-2">{Math.round(row.flood_probability * 100)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
