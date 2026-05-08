import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token from localStorage on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('fms_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect to login on 401
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('fms_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', { email, password }),
  register: (email: string, password: string, display_name: string) =>
    apiClient.post('/auth/register', { email, password, display_name }),
  me: () => apiClient.get('/auth/me'),
}

// ─── Geographic ───────────────────────────────────────────────────────────────
export const geoApi = {
  listAreas: (area_type?: string) =>
    apiClient.get('/geographic/areas', { params: area_type ? { area_type } : {} }),
  getArea: (id: number) => apiClient.get(`/geographic/areas/${id}`),
  createArea: (data: object) => apiClient.post('/geographic/areas', data),
  searchByBbox: (min_lat: number, min_lon: number, max_lat: number, max_lon: number) =>
    apiClient.get('/geographic/areas/search/bbox', { params: { min_lat, min_lon, max_lat, max_lon } }),
  listStations: (area_id?: number) =>
    apiClient.get('/geographic/stations', { params: area_id ? { area_id } : {} }),
  stationsGeoJSON: () => apiClient.get('/geographic/stations/geojson/all'),
  createStation: (data: object) => apiClient.post('/geographic/stations', data),
}

// ─── Sensors & Measurements ───────────────────────────────────────────────────
export const sensorApi = {
  listTypes: () => apiClient.get('/sensors/types'),
  listSensors: (station_id?: number) =>
    apiClient.get('/sensors/', { params: station_id ? { station_id } : {} }),
  getMeasurements: (station_id: number, start_time?: string, end_time?: string) =>
    apiClient.get(`/sensors/measurements/station/${station_id}`, {
      params: { start_time, end_time, limit: 200 }
    }),
  addMeasurement: (data: object) => apiClient.post('/sensors/measurements', data),
}

// ─── Flood Events ─────────────────────────────────────────────────────────────
export const eventsApi = {
  list: (params?: object) => apiClient.get('/events/', { params }),
  get: (id: number) => apiClient.get(`/events/${id}`),
  summary: () => apiClient.get('/events/summary/global'),
  areaRecent: (area_id: number) => apiClient.get(`/events/area/${area_id}/recent`),
}

// ─── Alerts ───────────────────────────────────────────────────────────────────
export const alertsApi = {
  list: (params?: object) => apiClient.get('/alerts/', { params }),
  get: (id: number) => apiClient.get(`/alerts/${id}`),
  updateStatus: (id: number, status: string, summary?: string) =>
    apiClient.patch(`/alerts/${id}/status`, { status, summary }),
  listRules: (area_id?: number) =>
    apiClient.get('/alerts/rules', { params: area_id ? { area_id } : {} }),
  createRule: (data: object) => apiClient.post('/alerts/rules', data),
  updateRule: (id: number, data: object) => apiClient.patch(`/alerts/rules/${id}`, data),
  deleteRule: (id: number) => apiClient.delete(`/alerts/rules/${id}`),
}

// ─── Ingestion ────────────────────────────────────────────────────────────────
export const ingestionApi = {
  triggerSentinel: (area_id: number, start_date: string, end_date: string, satellite: string) =>
    apiClient.post('/ingestion/trigger/sentinel', null, {
      params: { area_id, start_date, end_date, satellite }
    }),
  getJobStatus: (job_id: number) => apiClient.get(`/ingestion/jobs/${job_id}/status`),
  listJobs: () => apiClient.get('/ingestion/jobs'),
}
