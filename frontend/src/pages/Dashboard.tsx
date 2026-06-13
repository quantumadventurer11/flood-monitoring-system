import { Activity, AlertTriangle, ChevronDown, CloudRain, Compass, Gauge, Globe2, Info, MapPin, RefreshCw, Satellite, ShieldCheck } from "lucide-react";
import type React from "react";
import { useEffect, useMemo, useState } from "react";
import { api, type BatchPrediction, type Event, type Hotspot, type ModelStatus, type Prediction, type Region, type ValidationScenario } from "../api/client";
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
  operational_mode: "fallback_open_meteo_proxy",
  publishable: false,
  validation_status: "not_independently_validated",
  validation_note: "Run a prediction to see validation status.",
  rain_7d_mm: null,
  max_daily_rain_mm: null,
  water_signal: null,
  hotspots: [],
};

const formatMetric = (value?: number | null, suffix = "") => (typeof value === "number" ? `${value.toFixed(value >= 10 ? 1 : 2)}${suffix}` : "Pending");

const formatMode = (mode?: string) => (mode ? mode.replace(/_/g, " ") : "checking");

function riskSummary(risk: string) {
  if (risk === "High") return "Flood-like conditions are strong in this check. Review local alerts before making decisions.";
  if (risk === "Medium") return "Some flood signals are present. Watch the forecast and re-check nearby locations.";
  return "Current signals look low, but conditions can change quickly after heavy rain.";
}

function CollapsiblePanel({
  id,
  title,
  icon,
  open,
  onToggle,
  children,
}: {
  id: string;
  title: string;
  icon?: React.ReactNode;
  open: boolean;
  onToggle: (id: string) => void;
  children: React.ReactNode;
}) {
  return (
    <section className="card alive-card soft-panel overflow-hidden">
      <button
        aria-controls={`${id}-panel`}
        aria-expanded={open}
        className="interactive-button flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
        onClick={() => onToggle(id)}
        type="button"
      >
        <span className="flex min-w-0 items-center gap-2 font-semibold text-slate-800 dark:text-white">
          {icon}
          <span className="truncate">{title}</span>
        </span>
        <ChevronDown size={18} className={`shrink-0 text-slate-500 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div id={`${id}-panel`} className="border-t border-slate-100 px-4 py-3 dark:border-slate-800">
          {children}
        </div>
      )}
    </section>
  );
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
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [modelStatusError, setModelStatusError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState("Satellite terrain is visible underneath the country colors.");
  const [focusNonce, setFocusNonce] = useState(0);
  const [mapMarkerMode, setMapMarkerMode] = useState<"scenario" | "validation">("scenario");
  const [openPanels, setOpenPanels] = useState<Record<string, boolean>>({
    map: true,
    model: true,
    risk: true,
    quality: true,
    gauge: false,
    evidence: false,
    certainty: false,
    meaning: false,
    next: false,
    events: false,
  });

  useEffect(() => {
    const load = async () => {
      const [regionRows, eventRows, status] = await Promise.all([
        api.regions(),
        api.events(),
        api.modelStatus().catch((error) => {
          setModelStatusError(error instanceof Error ? error.message : "Model status unavailable.");
          return null;
        }),
      ]);
      setRegions(regionRows);
      setEvents(eventRows.slice(0, 10));
      if (status) {
        setModelStatus(status);
        setModelStatusError(null);
      }
    };
    load();
    const id = window.setInterval(load, 300000);
    return () => window.clearInterval(id);
  }, []);

  const handlePrediction = (result: CountryResult) => {
    setSelected({ country: result.country, lat: result.lat, lon: result.lon });
    setPrediction(result);
  };

  const togglePanel = (id: string) => {
    setOpenPanels((current) => ({ ...current, [id]: !current[id] }));
  };

  const resetMapView = () => {
    setFocusNonce((value) => value + 1);
  };

  const fitBangladeshScenario = () => {
    const markers = scenario?.ground_truth_hotspots ?? [];
    if (!markers.length) {
      resetMapView();
      return;
    }
    const lat = markers.reduce((sum, item) => sum + item.lat, 0) / markers.length;
    const lon = markers.reduce((sum, item) => sum + item.lon, 0) / markers.length;
    setSelected({ country: "Bangladesh", lat, lon });
    setFocusNonce((value) => value + 1);
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
    () => {
      if (mapMarkerMode === "validation" && scenario?.validation_hotspots?.length) {
        return scenario.validation_hotspots.map((item) => ({
          ...item,
          label: `Validation audit: ${(item.flood_class ?? item.risk_level).replace(/_/g, " ")}`,
          kind: "validation" as const,
        }));
      }
      return [
        ...((scenario?.ground_truth_hotspots ?? []) as Hotspot[]).map((item) => ({ ...item, label: "UNOSAT ground-truth flood patch", kind: "ground_truth" as const })),
        ...((scenario ? scenario.model_hotspots : prediction.hotspots ?? []) as Hotspot[]).slice(0, 8).map((item) => ({ ...item, label: "Model-indicated flood hotspot", kind: "model" as const })),
      ];
    },
    [mapMarkerMode, prediction.hotspots, scenario]
  );

  const isFallback = prediction.validation_status.includes("fallback") || prediction.data_source === "fallback";
  const backendFallback = modelStatus?.fallback_active ?? isFallback;
  const publishablePrediction = prediction.publishable && !isFallback;
  const probabilityPct = Math.round(prediction.flood_probability * 100);
  const confidencePct = Math.round(prediction.confidence * 100);
  const hasLivePrediction = prediction.validation_status !== "not_independently_validated";
  const statusTone = batchLoading ? "border-blue-200 bg-blue-50 text-blue-900 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-100" : scenario ? "border-cyan-200 bg-cyan-50 text-cyan-900 dark:border-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-100" : "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300";

  return (
    <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="card soft-panel min-w-0 overflow-hidden p-3">
        <div className="sticky top-2 z-[500] mb-3 flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50/95 p-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <p className="text-sm font-semibold uppercase text-blue-700 dark:text-cyan-300">Interactive flood map</p>
            <h2 className="mt-1 text-xl font-bold text-slate-900 dark:text-white sm:text-2xl">Click a country to run a fresh risk check</h2>
          </div>
          <div className="flex flex-wrap gap-2">
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
            <button
              className="interactive-button flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              onClick={scenario ? fitBangladeshScenario : resetMapView}
              type="button"
            >
              <RefreshCw size={16} />
              {scenario ? "Fit Bangladesh scenario" : "Reset view"}
            </button>
          </div>
        </div>
        <div className="map-overlay mb-3 grid min-w-0 gap-2 rounded-lg border border-slate-200 bg-white/95 p-3 dark:border-slate-800 dark:bg-slate-900/95 lg:grid-cols-[1fr_auto] lg:items-center">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold text-slate-900 dark:text-white">{countryFlag(selected.country)} {selected.country}</span>
            <span className={`rounded px-2 py-1 text-xs font-bold text-white ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{prediction.risk_level}</span>
            <span className="rounded bg-slate-100 px-2 py-1 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{probabilityPct}% likelihood</span>
            <span className="rounded bg-slate-100 px-2 py-1 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{confidencePct}% confidence</span>
            <span className="rounded bg-slate-100 px-2 py-1 capitalize text-slate-600 dark:bg-slate-800 dark:text-slate-300">{formatMode(prediction.operational_mode)}</span>
            <span className={`rounded px-2 py-1 font-semibold ${prediction.publishable ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200" : "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-200"}`}>
              {prediction.publishable ? "Publishable" : "Not publishable"}
            </span>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-full border border-cyan-200 bg-cyan-50 px-2 py-1 font-semibold text-cyan-800 dark:border-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-100">UNOSAT flood coordinate</span>
            <span className="rounded-full border border-red-200 bg-red-50 px-2 py-1 font-semibold text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-100">Model hotspot</span>
            {mapMarkerMode === "validation" && <span className="rounded-full border border-purple-200 bg-purple-50 px-2 py-1 font-semibold text-purple-800 dark:border-purple-800 dark:bg-purple-950/40 dark:text-purple-100">Validation class</span>}
          </div>
        </div>
        <FloodMap
          regions={regions}
          selected={selected}
          onSelect={setSelected}
          onPrediction={handlePrediction}
          externalResults={batchResults}
          hotspots={mapHotspots}
          focusNonce={focusNonce}
          className="h-[clamp(300px,calc(100vh-410px),540px)] min-h-0"
        />
      </section>
      <aside className="min-w-0 space-y-3 xl:max-h-[calc(100vh-132px)] xl:overflow-y-auto xl:pr-1">
        <CollapsiblePanel id="map" title="Map Mode" icon={<Satellite size={17} className={`${batchLoading ? "gentle-pulse" : ""} text-blue-700 dark:text-cyan-300`} />} open={openPanels.map} onToggle={togglePanel}>
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
            <div className="mt-3 space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <button
                  className={`interactive-button rounded border px-3 py-2 text-xs font-semibold ${mapMarkerMode === "scenario" ? "border-cyan-300 bg-cyan-50 text-cyan-900 dark:border-cyan-700 dark:bg-cyan-950/50 dark:text-cyan-100" : "border-slate-200 text-slate-700 dark:border-slate-700 dark:text-slate-200"}`}
                  onClick={() => setMapMarkerMode("scenario")}
                  type="button"
                >
                  Ground truth / model
                </button>
                <button
                  className={`interactive-button rounded border px-3 py-2 text-xs font-semibold ${mapMarkerMode === "validation" ? "border-purple-300 bg-purple-50 text-purple-900 dark:border-purple-700 dark:bg-purple-950/50 dark:text-purple-100" : "border-slate-200 text-slate-700 dark:border-slate-700 dark:text-slate-200"}`}
                  onClick={() => setMapMarkerMode("validation")}
                  type="button"
                  disabled={!scenario.validation_hotspots?.length}
                >
                  Validation classes
                </button>
              </div>
              <p className="rounded border border-cyan-200 bg-cyan-50 px-3 py-2 text-xs text-cyan-900 dark:border-cyan-800 dark:bg-cyan-950/40 dark:text-cyan-100">
                {scenario.title}: markers come from local UNOSAT-derived flood coordinates and local audit artifacts only.
              </p>
            </div>
          )}
        </CollapsiblePanel>
        <CollapsiblePanel id="quality" title="Evidence Quality" icon={<ShieldCheck size={17} className="text-emerald-700 dark:text-emerald-300" />} open={openPanels.quality} onToggle={togglePanel}>
          <div className="grid gap-2 text-xs">
            <div className="flex items-center justify-between gap-3 rounded border border-slate-100 px-3 py-2 dark:border-slate-800">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Ground truth</span>
              <span className="text-right text-cyan-700 dark:text-cyan-200">UNOSAT labels only</span>
            </div>
            <div className="flex items-center justify-between gap-3 rounded border border-slate-100 px-3 py-2 dark:border-slate-800">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Model signal</span>
              <span className="text-right text-slate-600 dark:text-slate-300">{modelStatus?.data_mode === "copernicus_sentinel" ? "Sentinel-backed" : "Fallback/proxy"}</span>
            </div>
            <div className="flex items-center justify-between gap-3 rounded border border-slate-100 px-3 py-2 dark:border-slate-800">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Forecast</span>
              <span className="text-right text-slate-600 dark:text-slate-300">Operational context</span>
            </div>
            <div className="flex items-center justify-between gap-3 rounded border border-slate-100 px-3 py-2 dark:border-slate-800">
              <span className="font-semibold text-slate-700 dark:text-slate-300">Audit artifact</span>
              <span className={`text-right font-semibold ${scenario?.validation_audit?.publishable ? "text-emerald-700 dark:text-emerald-300" : "text-amber-700 dark:text-amber-300"}`}>
                {scenario?.validation_audit?.artifact_status?.replace(/_/g, " ") ?? "load Bangladesh test"}
              </span>
            </div>
          </div>
          <p className="mt-3 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
            Validation labels, model probabilities, and forecast inputs are tracked as separate evidence tiers.
          </p>
        </CollapsiblePanel>
        <CollapsiblePanel id="model" title="Model Status" icon={backendFallback ? <AlertTriangle size={17} className="text-amber-700 dark:text-amber-300" /> : <ShieldCheck size={17} className="text-emerald-700 dark:text-emerald-300" />} open={openPanels.model} onToggle={togglePanel}>
          <div className="grid gap-2 text-sm">
            <div className="flex items-center justify-between gap-3 rounded border border-slate-100 px-3 py-2 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400">Backend</span>
              <strong className="text-slate-900 dark:text-slate-100">{modelStatus?.backend_status ?? (modelStatusError ? "error" : "checking")}</strong>
            </div>
            <div className="flex items-center justify-between gap-3 rounded border border-slate-100 px-3 py-2 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400">Data mode</span>
              <strong className="text-right capitalize text-slate-900 dark:text-slate-100">{formatMode(modelStatus?.data_mode)}</strong>
            </div>
            <div className="flex items-center justify-between gap-3 rounded border border-slate-100 px-3 py-2 dark:border-slate-800">
              <span className="text-slate-500 dark:text-slate-400">XGBoost model</span>
              <strong className="text-slate-900 dark:text-slate-100">{modelStatus?.model_loaded || modelStatus?.model_artifact_present ? "available" : "checking"}</strong>
            </div>
          </div>
          <p className={`mt-3 rounded border px-3 py-2 text-xs ${backendFallback ? "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200" : "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200"}`}>
            {modelStatusError ?? modelStatus?.note ?? "Checking hosted model readiness."}
          </p>
        </CollapsiblePanel>
        <CollapsiblePanel id="risk" title="Current Risk" open={openPanels.risk} onToggle={togglePanel}>
        <div className="risk-glow overflow-hidden rounded-md border border-slate-100 dark:border-slate-800">
          <div className={`h-2 ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-500" : "bg-green-600"}`} />
          <div className="p-4">
            <p className="text-sm text-slate-500 dark:text-slate-400">Current Risk</p>
            <div className="mt-1 flex items-start justify-between gap-3">
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{countryFlag(selected.country)} {selected.country}</h2>
              <span className={`rounded px-3 py-1 text-sm font-bold text-white ${prediction.risk_level === "High" ? "bg-red-600" : prediction.risk_level === "Medium" ? "bg-amber-600" : "bg-green-600"}`}>{prediction.risk_level}</span>
            </div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{hasLivePrediction ? riskSummary(prediction.risk_level) : "Select a country on the map to run a prediction."}</p>
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">Source: {isFallback ? "rainfall-based proxy" : "satellite scene"} · {formatMode(prediction.operational_mode)}</p>
          </div>
        </div>
        </CollapsiblePanel>
        <CollapsiblePanel id="gauge" title="Probability Gauge" icon={<Gauge size={17} className="text-amber-700 dark:text-amber-300" />} open={openPanels.gauge} onToggle={togglePanel}>
          <FloodGauge probability={prediction.flood_probability} compact framed={false} />
        </CollapsiblePanel>
        <CollapsiblePanel id="evidence" title="Why this result?" icon={<CloudRain size={17} className="text-blue-700 dark:text-cyan-300" />} open={openPanels.evidence} onToggle={togglePanel}>
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
              <dd className="font-semibold text-slate-900 dark:text-slate-100">{publishablePrediction ? "Satellite" : "Proxy"}</dd>
            </div>
          </dl>
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">These indicators are separate from independent ground-truth validation.</p>
        </CollapsiblePanel>
        <CollapsiblePanel id="certainty" title="How sure is it?" icon={<Gauge size={17} className="text-amber-700 dark:text-amber-300" />} open={openPanels.certainty} onToggle={togglePanel}>
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
              {publishablePrediction ? "Satellite-scene predictions should be exported and compared with UNOSAT labels before citation." : "Fallback forecasts are triage-only until Sentinel/Copernicus patch scores are validated against ground truth."}
            </p>
          </div>
        </CollapsiblePanel>
        <CollapsiblePanel id="meaning" title="What does this mean?" icon={<Info size={17} className="text-slate-700 dark:text-slate-300" />} open={openPanels.meaning} onToggle={togglePanel}>
          <p className="text-sm text-slate-700 dark:text-slate-300">{riskSummary(prediction.risk_level)}</p>
        </CollapsiblePanel>
        <CollapsiblePanel id="next" title="What to do next" icon={<Compass size={17} className="text-blue-700 dark:text-cyan-300" />} open={openPanels.next} onToggle={togglePanel}>
          <p className="mb-3 text-sm text-slate-700 dark:text-slate-300">Run the 5-day forecast for the selected place, then compare with official local warnings before acting.</p>
          <button className="interactive-button flex w-full items-center justify-center gap-2 rounded-md bg-flood px-4 py-2 font-semibold text-white shadow-sm hover:bg-blue-700" onClick={() => onOpenForecast(selected)}>
          <Activity size={17} />
          Run 5-Day Forecast
          </button>
        </CollapsiblePanel>
        <AlertBanner risk={prediction.risk_level} message={`${selected.country}: ${prediction.risk_level} flood risk at ${probabilityPct}% likelihood.`} />
        <CollapsiblePanel id="events" title="Recent Events" open={openPanels.events} onToggle={togglePanel}>
          <EventsTable rows={events} />
        </CollapsiblePanel>
      </aside>
    </div>
  );
}
