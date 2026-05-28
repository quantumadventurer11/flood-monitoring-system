import { useEffect, useMemo, useState } from "react";
import { api, type ForecastDay, type Region } from "../api/client";
import CountrySelector, { countries, type Country } from "../components/CountrySelector";
import ForecastChart from "../components/ForecastChart";

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

  useEffect(() => {
    api.regions().then(setRegions);
  }, []);

  useEffect(() => {
    if (initialPlace) setCountry(initialPlace);
  }, [initialPlace]);

  useEffect(() => {
    api.forecast({ country: country.country, lat: country.lat, lon: country.lon }).then((rows) => {
      setForecast(rows);
      setLastUpdated(new Date().toLocaleString());
    });
  }, [country]);

  return (
    <div className="space-y-5">
      <section className="card p-5">
        <div className="grid gap-4 md:grid-cols-[360px_1fr] md:items-end">
          <div>
            <h2 className="section-title">5-Day Operational Forecast</h2>
            <p className="mt-1 text-sm text-slate-600">Weather-driven extension using Open-Meteo forecast and flood APIs.</p>
            {lastUpdated && <p className="mt-1 text-xs text-slate-500">Last updated {lastUpdated}</p>}
          </div>
          <CountrySelector value={country} regions={regions} onChange={setCountry} />
        </div>
      </section>
      <section className="card p-5">
        <ForecastChart data={forecast} />
      </section>
      <section className="grid gap-3 md:grid-cols-5">
        {forecast.map((day) => (
          <div key={day.date} className="card p-4">
            <p className="text-sm font-semibold">{day.date}</p>
            <p className={`mt-2 text-2xl font-bold ${day.risk_level === "High" ? "text-red-600" : day.risk_level === "Medium" ? "text-amber-600" : "text-green-600"}`}>{Math.round(day.flood_likelihood * 100)}%</p>
            <span className={`inline-block rounded px-2 py-1 text-xs font-semibold text-white ${day.risk_level === "High" ? "bg-red-600" : day.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{day.risk_level}</span>
            <p className="mt-2 text-xs text-slate-500">{day.precipitation_mm} mm rain</p>
            <p className="text-xs text-slate-500">Soil moisture {day.soil_moisture}</p>
            <p className="text-xs text-slate-500">River discharge {day.river_discharge ?? "n/a"}</p>
            {day.warning && <p className="mt-1 text-xs text-amber-700">Fallback forecast used</p>}
          </div>
        ))}
      </section>
    </div>
  );
}
