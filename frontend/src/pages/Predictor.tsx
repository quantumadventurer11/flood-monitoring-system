import { useState } from "react";
import { api, type Prediction } from "../api/client";
import CountrySelector, { countries, type Country } from "../components/CountrySelector";
import FloodGauge from "../components/FloodGauge";
import FloodMap from "../components/Map";

export default function Predictor() {
  const [country, setCountry] = useState<Country>(countries[0]);
  const [date, setDate] = useState("2024-08-01");
  const [prediction, setPrediction] = useState<Prediction | null>(null);

  const submit = async () => {
    setPrediction(await api.predict({ country: country.country, lat: country.lat, lon: country.lon, date }));
  };

  return (
    <div className="grid gap-5 lg:grid-cols-[360px_1fr]">
      <section className="card space-y-4 p-5">
        <h2 className="section-title">Run Prediction</h2>
        <CountrySelector value={country} onChange={setCountry} />
        <input className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" type="date" value={date} onChange={(event) => setDate(event.target.value)} />
        <button className="w-full rounded-md bg-flood px-4 py-2 font-semibold text-white" onClick={submit}>Predict Flood Risk</button>
        {prediction && (
          <div className="space-y-3 pt-2">
            <FloodGauge probability={prediction.flood_probability} />
            <p className="text-sm text-slate-700">Classification: <strong>{prediction.classification}</strong></p>
            <p className="text-sm text-slate-700">Confidence: <strong>{Math.round(prediction.confidence * 100)}%</strong></p>
          </div>
        )}
      </section>
      <section className="card p-3">
        <FloodMap regions={[{ ...country, risk_level: prediction?.risk_level ?? "Medium" }]} selected={country} onSelect={() => undefined} />
      </section>
    </div>
  );
}
