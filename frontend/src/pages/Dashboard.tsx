import { useEffect, useState } from "react";
import { api, type Prediction } from "../api/client";
import AlertBanner from "../components/AlertBanner";
import EventsTable from "../components/EventsTable";
import FloodGauge from "../components/FloodGauge";
import FloodMap from "../components/Map";

export default function Dashboard() {
  const [regions, setRegions] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [selected, setSelected] = useState({ country: "Bangladesh", lat: 23.8103, lon: 90.4125 });
  const [prediction, setPrediction] = useState<Prediction>({ flood_probability: 0.91, risk_level: "High", classification: "flood", confidence: 0.91 });

  useEffect(() => {
    const load = async () => {
      setRegions(await api.regions());
      setEvents(await api.events());
    };
    load();
    const id = window.setInterval(load, 300000);
    return () => window.clearInterval(id);
  }, []);

  const onSelect = async (region: any) => {
    setSelected(region);
    const result = await api.predict({ country: region.country, lat: region.lat, lon: region.lon, date: new Date().toISOString().slice(0, 10) });
    setPrediction(result);
  };

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
      <section className="card min-h-[520px] p-3">
        <FloodMap regions={regions} selected={selected} onSelect={onSelect} />
      </section>
      <aside className="space-y-4">
        <FloodGauge probability={prediction.flood_probability} />
        <div className="card p-4">
          <p className="text-sm text-slate-500">Selected region</p>
          <h2 className="text-xl font-semibold">{selected.country}</h2>
          <span className={`mt-3 inline-block rounded px-3 py-1 text-sm font-bold text-white ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{prediction.risk_level}</span>
        </div>
        <AlertBanner risk={prediction.risk_level} message={`${selected.country}: ${prediction.risk_level} flood risk at ${Math.round(prediction.flood_probability * 100)}% likelihood.`} />
        <div className="card p-4">
          <h3 className="mb-3 font-semibold">Recent Events</h3>
          <EventsTable rows={events} />
        </div>
      </aside>
    </div>
  );
}
