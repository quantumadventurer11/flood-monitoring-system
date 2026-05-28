import { useEffect, useState } from "react";
import { api, type ForecastDay } from "../api/client";
import CountrySelector, { countries, type Country } from "../components/CountrySelector";
import ForecastChart from "../components/ForecastChart";

export default function Forecast() {
  const [country, setCountry] = useState<Country>(countries[0]);
  const [forecast, setForecast] = useState<ForecastDay[]>([]);

  useEffect(() => {
    api.forecast({ country: country.country, lat: country.lat, lon: country.lon }).then(setForecast);
  }, [country]);

  return (
    <div className="space-y-5">
      <section className="card p-5">
        <div className="grid gap-4 md:grid-cols-[320px_1fr] md:items-end">
          <div>
            <h2 className="section-title">5-Day Operational Forecast</h2>
            <p className="mt-1 text-sm text-slate-600">Weather-driven extension using Open-Meteo; separate from reproduced paper methodology.</p>
          </div>
          <CountrySelector value={country} onChange={setCountry} />
        </div>
      </section>
      <section className="card p-5">
        <ForecastChart data={forecast} />
      </section>
      <section className="grid gap-3 md:grid-cols-5">
        {forecast.map((day) => (
          <div key={day.date} className="card p-4">
            <p className="text-sm font-semibold">{day.date}</p>
            <p className="mt-2 text-2xl font-bold text-flood">{Math.round(day.flood_likelihood * 100)}%</p>
            <p className="text-sm text-slate-600">{day.risk_level} risk</p>
            <p className="mt-2 text-xs text-slate-500">{day.precipitation_mm} mm rain, soil {day.soil_moisture}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
