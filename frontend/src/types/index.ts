// ─── API types matching backend schemas ──────────────────────────────────────

export interface GeographicArea {
  area_id: number
  area_name: string
  area_type: string
  min_lat: number | null
  min_lon: number | null
  max_lat: number | null
  max_lon: number | null
  created_at: string
  stations?: Station[]
}

export interface Station {
  station_id: number
  area_id: number
  station_code: string
  station_name: string
  latitude: number
  longitude: number
  elevation_m: number | null
  status: string
  installed_at: string | null
}

export interface FloodEvent {
  flood_event_id: number
  model_run_id: number
  area_id: number
  detected_at: string
  event_start: string | null
  event_end: string | null
  confidence: 'LOW' | 'MEDIUM' | 'HIGH' | null
  summary: string | null
  impacts?: EventImpact[]
}

export interface EventImpact {
  impact_id: number
  flood_event_id: number
  impact_type: string
  severity: string | null
  estimated_area_sq_km: number | null
  estimated_people_affected: number | null
  notes: string | null
}

export interface Alert {
  alert_id: number
  alert_rule_id: number
  station_id: number
  user_id: number
  triggered_at: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: 'TRIGGERED' | 'ACKNOWLEDGED' | 'RESOLVED' | 'FALSE_POSITIVE'
  summary: string | null
  details_json: string | null
  acknowledged_at: string | null
}

export interface AlertRule {
  alert_rule_id: number
  station_id: number
  area_id: number
  rule_name: string
  metric: string
  operator: string
  threshold_value: number
  window_minutes: number
  severity: string
  is_enabled: boolean
  created_at: string
}

export interface Measurement {
  measurement_id: number
  station_id: number
  sensor_id: number
  observed_at: string
  value: number
  unit: string | null
  quality_flag: string | null
  ingested_at: string
}

export interface User {
  user_id: number
  email: string
  display_name: string
  role_id: number
  is_active: boolean
  created_at: string
  last_login_at: string | null
}

export interface Token {
  access_token: string
  token_type: string
  expires_in: number
}

export interface IngestJob {
  job_id: number
  status: string
  job_type: string
  started_at: string
  completed_at: string | null
  output_location: string | null
  errors: { code: string; message: string }[]
}

export interface GlobalSummary {
  total_events: number
  high_confidence_events: number
  medium_confidence_events: number
  recent_events: FloodEvent[]
}

// ─── UI state types ────────────────────────────────────────────────────────
export interface MapSelection {
  lat: number
  lng: number
  area?: GeographicArea | null
}

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
