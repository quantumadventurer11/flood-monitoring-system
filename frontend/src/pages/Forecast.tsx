import { useEffect, useMemo, useState } from "react";
import { api, type ForecastDay, type Region } from "../api/client";
import CountrySelector, { countries, type Country } from "../components/CountrySelector";
import ForecastChart from "../components/ForecastChart";

const statusTone = (status?: string) => {
  if (status === "ok") return "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-100";
  if (status === "weather_only") return "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100";
  if (status === "fallback") return "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-100";
  return "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200";
};

const formatStatus = (status?: string) => (status ? status.replace(/_/g, " ") : "checking");
const formatValue = (value: number | null | undefined, suffix = "") => (typeof value === "number" ? `${value}${suffix}` : "Unavailable");

export default function Forecast({ initialPlace }: { initialPlace?: Country | null }) {
  const queryPlace = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    const country = params.get("country");
    const lat = Number(params.get("lat"));
    const lon = Number(params.get("lon"));
    return country && Number.isFinite(lat) && Number.isFinite(lon) ? { country, lat, lon } : null;
  }, []);
  const [regions, setRegions] = useState<Region[]>([]);
  const [country, setCountry] = useState<Country>(initialPlace ?? queryPlace ?? countries[0]);
  const [forecast, setForecast] = useState<ForecastDay[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.regions().then(setRegions);
  }, []);

  useEffect(() => {
    if (initialPlace) setCountry(initialPlace);
  }, [initialPlace]);

  const loadForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await api.forecast({ country: country.country, lat: country.lat, lon: country.lon });
      setForecast(rows);
      setLastUpdated(new Date().toLocaleString());
    } catch (err) {
      setForecast([]);
      setError(err instanceof Error ? err.message : "Forecast request failed.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadForecast();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [country]);

  const currentStatus = forecast[0]?.forecast_status;
  const currentNote = error ?? forecast[0]?.status_note ?? "Select a place to load the latest forecast.";
  const weatherOnly = currentStatus === "weather_only";
  const fallback = currentStatus === "fallback";

  return (
    <div className="space-y-5">
      <section className="card p-5">
        <div className="grid gap-4 md:grid-cols-[360px_1fr] md:items-end">
          <div>
            <h2 className="section-title">5-Day Operational Forecast</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Weather-driven extension using Open-Meteo forecast and flood APIs.</p>
            {lastUpdated && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Last updated {lastUpdated}</p>}
          </div>
          <CountrySelector value={country} regions={regions} onChange={setCountry} />
        </div>
        <div className={`mt-4 rounded border px-3 py-2 text-sm capitalize ${statusTone(error ? "fallback" : currentStatus)}`}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <strong>{error ? "API error" : formatStatus(currentStatus)}</strong>
            <button className="rounded border border-current px-2 py-1 text-xs font-semibold normal-case" onClick={loadForecast} disabled={loading} type="button">
              {loading ? "Loading..." : "Retry"}
            </button>
          </div>
          <p className="mt-1 normal-case">{currentNote}</p>
        </div>
      </section>
      <section className="card p-5">
        {loading && !forecast.length ? (
          <div className="grid h-80 place-items-center text-sm text-slate-500 dark:text-slate-400">Loading forecast...</div>
        ) : forecast.length ? (
          <ForecastChart data={forecast} />
        ) : (
          <div className="grid h-80 place-items-center rounded border border-dashed border-slate-300 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">No forecast rows available.</div>
        )}
      </section>
      <section className="grid gap-3 md:grid-cols-5">
        {forecast.map((day) => (
          <div key={day.date} className="card p-4">
            <p className="text-sm font-semibold">{day.date}</p>
            <p className={`mt-2 text-2xl font-bold ${day.risk_level === "High" ? "text-red-600" : day.risk_level === "Medium" ? "text-amber-600" : "text-green-600"}`}>{Math.round(day.flood_likelihood * 100)}%</p>
            <span className={`inline-block rounded px-2 py-1 text-xs font-semibold text-white ${day.risk_level === "High" ? "bg-red-600" : day.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{day.risk_level}</span>
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{day.precipitation_mm} mm rain</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Soil moisture {formatValue(day.soil_moisture)}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">River discharge {formatValue(day.river_discharge, " m3/s")}</p>
            <p className="mt-2 text-xs font-semibold capitalize text-slate-600 dark:text-slate-300">{formatStatus(day.forecast_status)}</p>
            {weatherOnly && <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">River discharge unavailable</p>}
            {fallback && <p className="mt-1 text-xs text-red-700 dark:text-red-300">Fallback forecast used</p>}
          </div>
        ))}
      </section>
    </div>
  );
}
