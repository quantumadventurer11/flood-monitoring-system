import { CloudRain } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type Event, type Prediction, type Region } from "../api/client";
import AlertBanner from "../components/AlertBanner";
import { countryFlag } from "../components/CountrySelector";
import EventsTable from "../components/EventsTable";
import FloodGauge from "../components/FloodGauge";
import FloodMap, { type CountryResult, type SelectedPlace } from "../components/Map";

const defaultPrediction: Prediction = {
  flood_probability: 0.1,
  risk_level: "Low",
  classification: "no_flood",
  confidence: 0.9,
  data_source: "fallback",
  date: new Date().toISOString().slice(0, 10),
};

export default function Dashboard({ onOpenForecast }: { onOpenForecast: (place: SelectedPlace) => void }) {
  const [regions, setRegions] = useState<Region[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selected, setSelected] = useState<SelectedPlace>({ country: "Bangladesh", lat: 23.685, lon: 90.3563 });
  const [prediction, setPrediction] = useState<Prediction>(defaultPrediction);

  useEffect(() => {
    const load = async () => {
      setRegions(await api.regions());
      setEvents((await api.events()).slice(0, 10));
    };
    load();
    const id = window.setInterval(load, 300000);
    return () => window.clearInterval(id);
  }, []);

  const handlePrediction = (result: CountryResult) => {
    setSelected({ country: result.country, lat: result.lat, lon: result.lon });
    setPrediction(result);
  };

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
      <section className="card min-h-[620px] p-3">
        <FloodMap regions={regions} selected={selected} onSelect={setSelected} onPrediction={handlePrediction} />
      </section>
      <aside className="space-y-4">
        <div className="card p-4">
          <p className="text-sm text-slate-500">Selected country</p>
          <h2 className="text-xl font-semibold">{countryFlag(selected.country)} {selected.country}</h2>
          <span className={`mt-3 inline-block rounded px-3 py-1 text-sm font-bold text-white ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{prediction.risk_level}</span>
          <p className="mt-2 text-xs text-slate-500">Data source: {prediction.data_source}</p>
        </div>
        <FloodGauge probability={prediction.flood_probability} />
        <button className="flex w-full items-center justify-center gap-2 rounded-md bg-flood px-4 py-2 font-semibold text-white" onClick={() => onOpenForecast(selected)}>
          <CloudRain size={17} />
          Run 5-Day Forecast
        </button>
        <AlertBanner risk={prediction.risk_level} message={`${selected.country}: ${prediction.risk_level} flood risk at ${Math.round(prediction.flood_probability * 100)}% likelihood.`} />
        <div className="card p-4">
          <h3 className="mb-3 font-semibold">Recent Events</h3>
          <EventsTable rows={events} />
        </div>
      </aside>
    </div>
  );
}
