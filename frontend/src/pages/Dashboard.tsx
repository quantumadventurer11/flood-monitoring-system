import { Activity, CloudRain, Compass, Gauge, Globe2, Info, MapPin, Satellite } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, type BatchPrediction, type Event, type Hotspot, type Prediction, type Region, type ValidationScenario } from "../api/client";
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
  validation_status: "not_independently_validated",
  validation_note: "Run a prediction to see validation status.",
  rain_7d_mm: null,
  max_daily_rain_mm: null,
  water_signal: null,
  hotspots: [],
};

const formatMetric = (value?: number | null, suffix = "") => (typeof value === "number" ? `${value.toFixed(value >= 10 ? 1 : 2)}${suffix}` : "Pending");

function riskSummary(risk: string) {
  if (risk === "High") return "Flood-like conditions are strong in this check. Review local alerts before making decisions.";
  if (risk === "Medium") return "Some flood signals are present. Watch the forecast and re-check nearby locations.";
  return "Current signals look low, but conditions can change quickly after heavy rain.";
}

export default function Dashboard({ onOpenForecast }: { onOpenForecast: (place: SelectedPlace) => void }) {
  const [regions, setRegions] = useState<Region[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [selected, setSelected] = useState<SelectedPlace>({ country: "Bangladesh", lat: 23.685, lon: 90.3563 });
  const [prediction, setPrediction] = useState<Prediction>(defaultPrediction);
  const [batch, setBatch] = useState<BatchPrediction | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [scenario, setScenario] = useState<ValidationScenario | null>(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Satellite terrain is visible underneath the country colors.");

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

  const runBatch = async () => {
    setBatchLoading(true);
    setStatusMessage("Running the model for all monitored countries...");
    try {
      const result = await api.predictRegions(new Date().toISOString().slice(0, 10));
      setBatch(result);
      const firstHigh = result.results.find((item) => item.prediction?.risk_level === "High") ?? result.results.find((item) => item.prediction);
      if (firstHigh?.prediction) {
        handlePrediction({ country: firstHigh.country, lat: firstHigh.lat, lon: firstHigh.lon, ...firstHigh.prediction });
      }
      setStatusMessage(`Completed ${result.completed} of ${result.total} monitored countries.`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Batch prediction failed.");
    } finally {
      setBatchLoading(false);
    }
  };

  const runBangladeshScenario = async () => {
    setScenarioLoading(true);
    setStatusMessage("Loading the Bangladesh 2024 UNOSAT ground-truth scenario...");
    try {
      const result = await api.bangladeshScenario();
      setScenario(result);
      setSelected({ country: "Bangladesh", lat: 23.685, lon: 90.3563 });
      setPrediction(result.prediction);
      setStatusMessage("Bangladesh 2024 scenario loaded with model and UNOSAT coordinate markers.");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Bangladesh scenario failed.");
    } finally {
      setScenarioLoading(false);
    }
  };

  const batchResults = useMemo(
    () =>
      Object.fromEntries(
        (batch?.results ?? [])
          .filter((item) => item.prediction)
          .map((item) => [item.country, { country: item.country, lat: item.lat, lon: item.lon, ...(item.prediction as Prediction) }])
      ) as Record<string, CountryResult>,
    [batch]
  );

  const mapHotspots = useMemo(
    () => [
      ...((scenario?.ground_truth_hotspots ?? []) as Hotspot[]).map((item) => ({ ...item, label: "UNOSAT ground-truth flood patch", kind: "ground_truth" as const })),
      ...((scenario ? scenario.model_hotspots : prediction.hotspots ?? []) as Hotspot[]).slice(0, 8).map((item) => ({ ...item, label: "Model-indicated flood hotspot", kind: "model" as const })),
    ],
    [prediction.hotspots, scenario]
  );

  const isFallback = prediction.validation_status.includes("fallback") || prediction.data_source === "fallback";
  const probabilityPct = Math.round(prediction.flood_probability * 100);
  const confidencePct = Math.round(prediction.confidence * 100);
  const hasLivePrediction = prediction.validation_status !== "not_independently_validated";
  const statusTone = batchLoading ? "border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-100" : scenario ? "border-cyan-200 bg-cyan-50 text-cyan-900 dark:border-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-100" : "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300";

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section className="card soft-panel min-h-[620px] overflow-hidden p-3">
        <div className="mb-3 flex flex-col gap-3 rounded-lg bg-slate-50 p-4 dark:bg-slate-950/60 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase text-blue-700 dark:text-cyan-300">Interactive flood map</p>
            <h2 className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">Click a country to run a fresh risk check</h2>
            <p className="mt-1 max-w-2xl text-sm text-slate-600 dark:text-slate-400">Satellite terrain is shown underneath. Country colors show model risk, and markers show specific flood-region coordinates.</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button
              className="interactive-button flex items-center justify-center gap-2 rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-950"
              onClick={runBatch}
              disabled={batchLoading}
            >
              <Globe2 size={16} />
              {batchLoading ? "Running all..." : "Run all monitored countries"}
            </button>
            <button
              className="interactive-button flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              onClick={runBangladeshScenario}
              disabled={scenarioLoading}
            >
              <MapPin size={16} />
              {scenarioLoading ? "Loading test..." : "Bangladesh 2024 test"}
            </button>
          </div>
        </div>
        <div className="map-overlay mb-3 grid gap-2 rounded-lg border border-slate-200 bg-white/95 p-3 dark:border-slate-800 dark:bg-slate-900/95 md:grid-cols-[1fr_auto] md:items-center">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold text-slate-900 dark:text-white">{countryFlag(selected.country)} {selected.country}</span>
            <span className={`rounded px-2 py-1 text-xs font-bold text-white ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{prediction.risk_level}</span>
            <span className="text-slate-500 dark:text-slate-400">{probabilityPct}% likelihood</span>
            <span className="text-slate-500 dark:text-slate-400">{confidencePct}% confidence</span>
            <span className="text-slate-500 dark:text-slate-400">{prediction.data_source}</span>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-full border border-cyan-200 bg-cyan-50 px-2 py-1 font-semibold text-cyan-800 dark:border-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-100">UNOSAT flood coordinate</span>
            <span className="rounded-full border border-red-200 bg-red-50 px-2 py-1 font-semibold text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-100">Model hotspot</span>
          </div>
        </div>
        <FloodMap regions={regions} selected={selected} onSelect={setSelected} onPrediction={handlePrediction} externalResults={batchResults} hotspots={mapHotspots} />
      </section>
      <aside className="space-y-4">
        <div className={`card alive-card soft-panel p-4 ${batchLoading ? "status-sweep" : ""}`}>
          <div className="mb-3 flex items-center gap-2">
            <Satellite size={17} className={`${batchLoading ? "gentle-pulse" : ""} text-blue-700 dark:text-cyan-300`} />
            <h3 className="font-semibold text-slate-800 dark:text-white">Map Mode</h3>
          </div>
          <p className={`relative rounded border px-3 py-2 text-sm ${statusTone}`}>{statusMessage}</p>
          {batch && (
            <div className="mt-3 grid grid-cols-4 gap-2 text-center text-xs">
              <div className="alive-card rounded bg-slate-100 p-2 dark:bg-slate-900"><strong className="block text-lg text-slate-900 dark:text-white">{batch.completed}/{batch.total}</strong>Done</div>
              <div className="alive-card rounded bg-red-50 p-2 text-red-700 dark:bg-red-950/40 dark:text-red-200"><strong className="block text-lg">{batch.high}</strong>High</div>
              <div className="alive-card rounded bg-amber-50 p-2 text-amber-700 dark:bg-amber-950/40 dark:text-amber-200"><strong className="block text-lg">{batch.medium}</strong>Med</div>
              <div className="alive-card rounded bg-green-50 p-2 text-green-700 dark:bg-green-950/40 dark:text-green-200"><strong className="block text-lg">{batch.low}</strong>Low</div>
            </div>
          )}
          {scenario && (
            <p className="mt-3 rounded border border-cyan-200 bg-cyan-50 px-3 py-2 text-xs text-cyan-900 dark:border-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-100">
              {scenario.title}: blue markers are local UNOSAT-derived flood coordinates. Click any marker to see its class, source details, and data fields.
            </p>
          )}
        </div>
        <div className="card risk-glow soft-panel alive-card overflow-hidden">
          <div className={`h-2 ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-500" : "bg-green-600"}`} />
          <div className="p-4">
            <p className="text-sm text-slate-500 dark:text-slate-400">Current Risk</p>
            <div className="mt-1 flex items-start justify-between gap-3">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{countryFlag(selected.country)} {selected.country}</h2>
              <span className={`rounded px-3 py-1 text-sm font-bold text-white ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{prediction.risk_level}</span>
            </div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{hasLivePrediction ? riskSummary(prediction.risk_level) : "Select a country on the map to run a prediction."}</p>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">Source: {isFallback ? "rainfall-based proxy" : "satellite scene"} · {prediction.data_source}</p>
          </div>
        </div>
        <FloodGauge probability={prediction.flood_probability} />
        <div className="card alive-card soft-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <CloudRain size={17} className="text-blue-700 dark:text-cyan-300" />
            <h3 className="font-semibold text-slate-800 dark:text-white">Why this result?</h3>
          </div>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div className="alive-card rounded border border-slate-100 p-2 dark:border-slate-800">
              <dt className="text-xs text-slate-500 dark:text-slate-400">Rain in 7 days</dt>
              <dd className="font-semibold text-slate-900 dark:text-slate-100">{formatMetric(prediction.rain_7d_mm, " mm")}</dd>
            </div>
            <div className="alive-card rounded border border-slate-100 p-2 dark:border-slate-800">
              <dt className="text-xs text-slate-500 dark:text-slate-400">Wettest day</dt>
              <dd className="font-semibold text-slate-900 dark:text-slate-100">{formatMetric(prediction.max_daily_rain_mm, " mm")}</dd>
            </div>
            <div className="alive-card rounded border border-slate-100 p-2 dark:border-slate-800">
              <dt className="text-xs text-slate-500 dark:text-slate-400">Water signal</dt>
              <dd className="font-semibold text-slate-900 dark:text-slate-100">{formatMetric(prediction.water_signal)}</dd>
            </div>
            <div className="alive-card rounded border border-slate-100 p-2 dark:border-slate-800">
              <dt className="text-xs text-slate-500 dark:text-slate-400">Check type</dt>
              <dd className="font-semibold text-slate-900 dark:text-slate-100">{isFallback ? "Proxy" : "Satellite"}</dd>
            </div>
          </dl>
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">These indicators are separate from independent ground-truth validation.</p>
        </div>
        <div className="card alive-card soft-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <Gauge size={17} className="text-amber-700 dark:text-amber-300" />
            <h3 className="font-semibold text-slate-800 dark:text-white">How sure is it?</h3>
          </div>
          <div className="space-y-3 text-sm">
            <div>
              <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>Flood likelihood</span>
                <span>{probabilityPct}%</span>
              </div>
              <div className="mt-1 h-2 rounded bg-slate-200 dark:bg-slate-800">
                <div className={`h-2 rounded ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-500" : "bg-green-600"}`} style={{ width: `${probabilityPct}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>Displayed confidence</span>
                <span>{confidencePct}%</span>
              </div>
              <div className="mt-1 h-2 rounded bg-slate-200 dark:bg-slate-800">
                <div className="h-2 rounded bg-slate-700 dark:bg-slate-300" style={{ width: `${confidencePct}%` }} />
              </div>
            </div>
            <p className={`rounded border px-3 py-2 text-xs ${isFallback ? "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200" : "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200"}`}>
              {isFallback ? "Fallback forecasts are triage-only until Sentinel/Copernicus patch scores are validated against ground truth." : "Satellite-scene predictions should be exported and compared with UNOSAT labels before citation."}
            </p>
          </div>
        </div>
        <div className="card alive-card soft-panel p-4">
          <div className="mb-2 flex items-center gap-2">
            <Info size={17} className="text-slate-700 dark:text-slate-300" />
            <h3 className="font-semibold text-slate-800 dark:text-white">What does this mean?</h3>
          </div>
          <p className="text-sm text-slate-700 dark:text-slate-300">{riskSummary(prediction.risk_level)}</p>
        </div>
        <div className="card alive-card soft-panel p-4">
          <div className="mb-2 flex items-center gap-2">
            <Compass size={17} className="text-blue-700 dark:text-cyan-300" />
            <h3 className="font-semibold text-slate-800 dark:text-white">What to do next</h3>
          </div>
          <p className="mb-3 text-sm text-slate-700 dark:text-slate-300">Run the 5-day forecast for the selected place, then compare with official local warnings before acting.</p>
          <button className="interactive-button flex w-full items-center justify-center gap-2 rounded-md bg-flood px-4 py-2 font-semibold text-white shadow-sm hover:bg-blue-700" onClick={() => onOpenForecast(selected)}>
          <Activity size={17} />
          Run 5-Day Forecast
          </button>
        </div>
        <AlertBanner risk={prediction.risk_level} message={`${selected.country}: ${prediction.risk_level} flood risk at ${probabilityPct}% likelihood.`} />
        <div className="card alive-card soft-panel p-4">
          <h3 className="mb-3 font-semibold text-slate-900 dark:text-white">Recent Events</h3>
          <EventsTable rows={events} />
        </div>
      </aside>
    </div>
  );
}
