const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type PaperResults = {
  dataset_stats: Array<{ month: string; date: string; total_patches: number; flooded_percent: number }>;
  model_metrics: Array<{ rank: number; model: string; roc_auc: number; accuracy: string; precision: string; recall: string; f1: number; training_time_s?: number }>;
  ablation_results: Array<{ configuration: string; features: number; roc_auc: number; accuracy: number; precision: number; recall: number; f1: number; time_s: number }>;
  confusion_matrices: Array<{ model: string; test_patches: number; missed_floods: number; false_positives: number }>;
  sensitivity_analysis: Record<string, string>;
  key_features: Array<{ rank: number; feature: string; description: string }>;
  paper_notes: string[];
};

export type Prediction = {
  flood_probability: number;
  risk_level: string;
  classification: string;
  confidence: number;
};

export type ForecastDay = {
  date: string;
  flood_likelihood: number;
  risk_level: string;
  precipitation_mm: number;
  soil_moisture: number;
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
  events: () => request<any[]>("/events"),
  alerts: () => request<any[]>("/alerts"),
  regions: () => request<any[]>("/regions"),
  predict: (body: { country: string; lat: number; lon: number; date: string }) =>
    request<Prediction>("/predict", { method: "POST", body: JSON.stringify(body) }),
  forecast: (body: { country: string; lat: number; lon: number }) =>
    request<ForecastDay[]>("/forecast", { method: "POST", body: JSON.stringify(body) }),
};
