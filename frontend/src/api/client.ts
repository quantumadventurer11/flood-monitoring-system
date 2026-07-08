const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type PaperResults = {
  dataset_stats: Array<{ month: string; date: string; total_patches: number; flooded_percent: number }>;
  model_metrics: Array<{ rank: number; model: string; roc_auc: number; accuracy: string; precision: string; recall: string; f1: number; training_time_s?: number; result_status?: string; note?: string }>;
  ablation_results: Array<{ configuration: string; features: number; roc_auc: number; accuracy: number; precision: number; recall: number; f1: number; time_s: number; result_status?: string }>;
  confusion_matrices: Array<{ model: string; test_patches: number; missed_floods: number; false_positives: number; true_positives?: number; true_negatives?: number; result_status?: string }>;
  metric_audit: Array<{ item: string; table_a1_value?: number; resolved_value?: number; status: string; note: string }>;
  independent_validation: {
    evidence_tiers?: Array<{ tier: string; source: string; role: string }>;
    source: {
      name: string;
      product_id: string;
      title: string;
      source_url: string;
      shapefile_url: string;
      event_code: string;
      sensor: string;
      acquisition_window: string;
      published: string;
      reported_flooded_area_km2: number;
      reported_receded_area_km2: number;
      reported_exposed_population: number;
      caveat: string;
    };
    ground_truth: { patches: number; flooded_patches: number; flooded_percent: number; grid: string };
    metric_status: string;
    metric_note: string;
    score_artifact?: string;
    first_principles_note?: string;
    patch_audit_artifact?: string;
    summary_artifact?: string;
    failure_analysis_artifact?: string;
    buffer_ablation_artifact?: string;
    ndwi_threshold_metrics?: {
      patches: number;
      roc_auc: number;
      accuracy: number;
      precision: number;
      recall: number;
      f1: number;
      confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
    };
    model_probability_metrics?: {
      patches: number;
      roc_auc: number;
      accuracy: number;
      precision: number;
      recall: number;
      f1: number;
      confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
    };
    failure_case_summary?: {
      false_positives: number;
      false_negatives: number;
      true_positives: number;
      true_negatives: number;
      note: string;
    };
    operational_fallback_audit?: {
      metric_status: string;
      sample: string;
      model_probability_metrics: {
        patches: number;
        roc_auc: number;
        accuracy: number;
        precision: number;
        recall: number;
        f1: number;
        confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
      };
      verdict: string;
    };
  };
  modularity_evidence: string[];
  methodology_references: Array<{
    key: string;
    title: string;
    authors: string;
    year: number;
    venue: string;
    doi: string;
    citation: string;
    relevance: string;
  }>;
  sensitivity_analysis: Record<string, string>;
  key_features: Array<{ rank: number; feature: string; description: string }>;
  paper_notes: string[];
};

export type Prediction = {
  flood_probability: number;
  risk_level: string;
  classification: string;
  confidence: number;
  data_source: string;
  date: string;
  operational_mode: string;
  publishable: boolean;
  validation_status: string;
  validation_note?: string | null;
  rain_7d_mm?: number | null;
  max_daily_rain_mm?: number | null;
  water_signal?: number | null;
  hotspots: Hotspot[];
};

export type Hotspot = {
  lat: number;
  lon: number;
  probability: number;
  risk_level: string;
  source: string;
  flood_class?: string | null;
  details?: Record<string, string | number | null>;
  data?: Record<string, string | number | null>;
};

export type BatchPredictionItem = {
  country: string;
  lat: number;
  lon: number;
  status: string;
  error?: string | null;
  prediction?: Prediction | null;
};

export type BatchPrediction = {
  date: string;
  scope: string;
  compute_mode: string;
  total: number;
  completed: number;
  failed: number;
  high: number;
  medium: number;
  low: number;
  results: BatchPredictionItem[];
};

export type ValidationScenario = {
  key: string;
  title: string;
  source: { event_code: string; name: string; title: string; source_url: string; acquisition_window: string; caveat: string };
  event_date: string;
  note: string;
  ground_truth_hotspots: Hotspot[];
  model_hotspots: Hotspot[];
  validation_hotspots: Hotspot[];
  validation_audit: {
    artifact_status?: string;
    publishable?: boolean;
    artifact?: string;
    patches?: number;
    error_type_counts?: Record<string, number>;
    note?: string;
  };
  prediction: Prediction;
};

export type ModelStatus = {
  backend_status: string;
  model_loaded: boolean;
  model_artifact_present: boolean;
  model_type: string;
  data_mode: string;
  fallback_active: boolean;
  copernicus_credentials_configured: boolean;
  publishable_predictions: boolean;
  validation_status: string;
  note: string;
};

export type ForecastDay = {
  date: string;
  flood_likelihood: number;
  risk_level: string;
  precipitation_mm: number;
  soil_moisture: number | null;
  river_discharge: number | null;
  warning: boolean;
  data_source: string;
  forecast_status: string;
  status_note?: string | null;
  river_discharge_status?: string | null;
};

export type Region = {
  id: number;
  country: string;
  lat: number;
  lon: number;
  buffer_km: number;
  risk_level?: string;
  risk_baseline: number;
};

export type Event = {
  id: number;
  country: string;
  event_date: string;
  flood_probability: number;
  risk_level: string;
  classification: string;
  source: string;
};

export type Alert = {
  id: number;
  country: string;
  message: string;
  risk_level: string;
  created_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  paperResults: () => request<PaperResults>("/paper-results"),
  modelStatus: () => request<ModelStatus>("/model-status"),
  events: () => request<Event[]>("/events"),
  alerts: () => request<Alert[]>("/alerts"),
  regions: () => request<Region[]>("/regions"),
  predict: (body: { country: string; lat: number; lon: number; date: string }) =>
    request<Prediction>("/predict", { method: "POST", body: JSON.stringify(body) }),
  predictRegions: (date: string) =>
    request<BatchPrediction>("/predict/batch/regions", { method: "POST", body: JSON.stringify({ date }) }),
  bangladeshScenario: () => request<ValidationScenario>("/validation/scenarios/bangladesh-2024"),
  forecast: (body: { country: string; lat: number; lon: number }) =>
    request<ForecastDay[]>("/forecast", { method: "POST", body: JSON.stringify(body) }),
};
