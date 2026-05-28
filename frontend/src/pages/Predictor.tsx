import { CloudRain, MapPin } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, type Prediction, type Region } from "../api/client";
import CountrySelector, { countries, type Country } from "../components/CountrySelector";
import FloodGauge from "../components/FloodGauge";
import FloodMap, { type SelectedPlace } from "../components/Map";

export default function Predictor({ onOpenForecast }: { onOpenForecast: (place: SelectedPlace) => void }) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const [regions, setRegions] = useState<Region[]>([]);
  const [country, setCountry] = useState<Country>(countries[0]);
  const [date, setDate] = useState(today);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [recent, setRecent] = useState<Array<SelectedPlace & Prediction>>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.regions().then((rows) => {
      setRegions(rows);
      if (rows.length) setCountry(rows[0]);
    });
  }, []);

  const submit = async () => {
    setLoading(true);
    try {
      const result = await api.predict({ country: country.country, lat: country.lat, lon: country.lon, date });
      setPrediction(result);
      setRecent((items) => [{ ...country, ...result }, ...items].slice(0, 5));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-5 lg:grid-cols-[380px_1fr]">
      <section className="card space-y-4 p-5">
        <h2 className="section-title">Worldwide Predictor</h2>
        <CountrySelector value={country} regions={regions} onChange={setCountry} />
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700">Date</span>
          <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type="date" value={date} onChange={(event) => setDate(event.target.value)} />
        </label>
        <button className="w-full rounded-md bg-flood px-4 py-2 font-semibold text-white disabled:opacity-60" onClick={submit} disabled={loading}>
          {loading ? "Running satellite pipeline..." : "Predict Flood Risk"}
        </button>
        {prediction && (
          <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <FloodGauge probability={prediction.flood_probability} />
            <p className="text-sm text-slate-700">Risk level: <strong>{prediction.risk_level}</strong></p>
            <p className="text-sm text-slate-700">Classification: <strong>{prediction.classification}</strong></p>
            <p className="text-sm text-slate-700">Confidence: <strong>{Math.round(prediction.confidence * 100)}%</strong></p>
            <p className="text-sm text-slate-700">Data source: <strong>{prediction.data_source === "copernicus" ? "Copernicus satellite" : "Fallback weather proxy"}</strong></p>
            <p className="text-sm text-slate-700">Satellite date: <strong>{prediction.date}</strong></p>
            <button className="flex w-full items-center justify-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white" onClick={() => onOpenForecast(country)}>
              <CloudRain size={16} />
              View 5-Day Forecast
            </button>
          </div>
        )}
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Recent Searches</h3>
          <div className="mt-2 space-y-2">
            {recent.map((item, index) => (
              <button key={`${item.country}-${index}`} className="flex w-full items-center justify-between rounded-md bg-white px-3 py-2 text-left text-sm" onClick={() => setCountry(item)}>
                <span>{item.country}</span>
                <span className="font-semibold">{Math.round(item.flood_probability * 100)}%</span>
              </button>
            ))}
            {!recent.length && <p className="text-sm text-slate-500">No searches yet.</p>}
          </div>
        </div>
      </section>
      <section className="card p-3">
        <div className="mb-2 flex items-center gap-2 text-sm text-slate-600"><MapPin size={16} /> Click the map to select a custom point.</div>
        <FloodMap regions={regions} selected={country} onSelect={(place) => setCountry(place)} allowPointSelect />
      </section>
    </div>
  );
}
