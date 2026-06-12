import { ChevronDown, CloudRain, MapPin } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, type Prediction, type Region } from "../api/client";
import CountrySelector, { countries, type Country } from "../components/CountrySelector";
import FloodGauge from "../components/FloodGauge";
import FloodMap, { type SelectedPlace } from "../components/Map";

const formatMode = (mode: string) => mode.replace(/_/g, " ");

export default function Predictor({ onOpenForecast }: { onOpenForecast: (place: SelectedPlace) => void }) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const [regions, setRegions] = useState<Region[]>([]);
  const [country, setCountry] = useState<Country>(countries[0]);
  const [date, setDate] = useState(today);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [recent, setRecent] = useState<Array<SelectedPlace & Prediction>>([]);
  const [loading, setLoading] = useState(false);
  const [customMode, setCustomMode] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);

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
    <div className="grid min-w-0 gap-5 lg:grid-cols-[minmax(320px,380px)_1fr]">
      <section className="card space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="section-title">Worldwide Predictor</h2>
          <div className="flex rounded-md border border-slate-200 bg-slate-100 p-1 text-sm dark:border-slate-800 dark:bg-slate-950">
            <button className={`rounded px-3 py-1.5 font-semibold ${!customMode ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white" : "text-slate-600 dark:text-slate-400"}`} onClick={() => setCustomMode(false)} type="button">
              Country
            </button>
            <button className={`rounded px-3 py-1.5 font-semibold ${customMode ? "bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white" : "text-slate-600 dark:text-slate-400"}`} onClick={() => setCustomMode(true)} type="button">
              Custom point
            </button>
          </div>
        </div>
        {!customMode ? (
          <CountrySelector value={country} regions={regions} onChange={setCountry} />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block sm:col-span-2">
              <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Label</span>
              <input className="form-control" value={country.country} onChange={(event) => setCountry({ ...country, country: event.target.value })} placeholder="Custom point" />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Latitude</span>
              <input className="form-control" type="number" step="0.0001" value={country.lat} onChange={(event) => setCountry({ ...country, lat: Number(event.target.value) })} />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Longitude</span>
              <input className="form-control" type="number" step="0.0001" value={country.lon} onChange={(event) => setCountry({ ...country, lon: Number(event.target.value) })} />
            </label>
          </div>
        )}
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">Date</span>
          <input className="form-control" type="date" value={date} onChange={(event) => setDate(event.target.value)} />
        </label>
        <button className="w-full rounded-md bg-flood px-4 py-2 font-semibold text-white disabled:opacity-60" onClick={submit} disabled={loading}>
          {loading ? "Running satellite pipeline..." : "Predict Flood Risk"}
        </button>
        {prediction && (
          <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/70">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Result</p>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">{country.country}</h3>
              </div>
              <span className={`rounded px-3 py-1 text-sm font-bold text-white ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{prediction.risk_level}</span>
            </div>
            <FloodGauge probability={prediction.flood_probability} compact framed={false} />
            {!prediction.publishable && (
              <p className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">{prediction.validation_note}</p>
            )}
            <button
              aria-expanded={detailsOpen}
              className="interactive-button flex w-full items-center justify-between rounded border border-slate-200 bg-white px-3 py-2 text-left text-sm font-semibold text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
              onClick={() => setDetailsOpen((open) => !open)}
              type="button"
            >
              Details
              <ChevronDown size={16} className={`transition-transform ${detailsOpen ? "rotate-180" : ""}`} />
            </button>
            {detailsOpen && (
              <dl className="grid gap-2 text-sm text-slate-700 dark:text-slate-300">
                <div className="flex justify-between gap-3"><dt>Classification</dt><dd className="font-semibold">{prediction.classification}</dd></div>
                <div className="flex justify-between gap-3"><dt>Confidence</dt><dd className="font-semibold">{Math.round(prediction.confidence * 100)}%</dd></div>
                <div className="flex justify-between gap-3"><dt>Data mode</dt><dd className="text-right font-semibold capitalize">{formatMode(prediction.operational_mode)}</dd></div>
                <div className="flex justify-between gap-3"><dt>Publication status</dt><dd className="text-right font-semibold">{prediction.publishable ? "Ready for export audit" : "Not publishable validation output"}</dd></div>
                <div className="flex justify-between gap-3"><dt>Satellite date</dt><dd className="font-semibold">{prediction.date}</dd></div>
              </dl>
            )}
            <button className="flex w-full items-center justify-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white" onClick={() => onOpenForecast(country)}>
              <CloudRain size={16} />
              View 5-Day Forecast
            </button>
          </div>
        )}
        <div>
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Recent Searches</h3>
          <div className="mt-2 space-y-2">
            {recent.map((item, index) => (
              <button key={`${item.country}-${index}`} className="flex w-full items-center justify-between rounded-md bg-white px-3 py-2 text-left text-sm text-slate-800 shadow-sm dark:bg-slate-900 dark:text-slate-100" onClick={() => setCountry(item)}>
                <span>{item.country}</span>
                <span className="font-semibold">{Math.round(item.flood_probability * 100)}%</span>
              </button>
            ))}
            {!recent.length && <p className="text-sm text-slate-500">No searches yet.</p>}
          </div>
        </div>
      </section>
      <section className="card min-w-0 p-3">
        <div className="mb-2 flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300"><MapPin size={16} /> Click the map to select a custom point.</div>
        <FloodMap
          regions={regions}
          selected={country}
          onSelect={(place) => {
            setCountry(place);
            setCustomMode(true);
          }}
          allowPointSelect
          className="h-[clamp(360px,calc(100vh-260px),680px)] min-h-0"
        />
      </section>
    </div>
  );
}
