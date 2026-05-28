import { Download } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import EventsTable from "../components/EventsTable";

export default function HistoryPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  useEffect(() => { api.events().then(setRows); }, []);
  const filtered = useMemo(() => rows.filter((row) => JSON.stringify(row).toLowerCase().includes(query.toLowerCase())), [rows, query]);

  const exportCsv = () => {
    const csv = ["date,country,risk,probability", ...filtered.map((r) => `${r.event_date},${r.country},${r.risk_level},${r.flood_probability}`)].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "flood-events.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="card p-5">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <h2 className="section-title">Flood Event History</h2>
        <div className="flex gap-2">
          <input className="rounded-md border border-slate-300 px-3 py-2 text-sm" placeholder="Search events" value={query} onChange={(event) => setQuery(event.target.value)} />
          <button className="flex items-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white" onClick={exportCsv}><Download size={16} /> CSV</button>
        </div>
      </div>
      <EventsTable rows={filtered} />
    </section>
  );
}
