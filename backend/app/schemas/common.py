from datetime import date, datetime
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    country: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    buffer_km: float = Field(gt=0, le=500)
    start_date: date
    end_date: date


class IngestResponse(BaseModel):
    status: str
    patches_processed: int


class PredictRequest(BaseModel):
    country: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    date: date


class HotspotOut(BaseModel):
    lat: float
    lon: float
    probability: float
    risk_level: str
    source: str
    flood_class: str | None = None
    details: dict[str, str | int | float | None] = {}
    data: dict[str, str | int | float | None] = {}


class PredictResponse(BaseModel):
    flood_probability: float
    risk_level: str
    classification: str
    confidence: float
    data_source: str
    date: date
    operational_mode: str = "fallback_proxy"
    publishable: bool = False
    validation_status: str = "not_independently_validated"
    validation_note: str | None = None
    rain_7d_mm: float | None = None
    max_daily_rain_mm: float | None = None
    water_signal: float | None = None
    hotspots: list[HotspotOut] = []


class ModelStatusResponse(BaseModel):
    backend_status: str
    model_loaded: bool
    model_artifact_present: bool
    model_type: str
    data_mode: str
    fallback_active: bool
    copernicus_credentials_configured: bool
    publishable_predictions: bool
    validation_status: str
    note: str


class BatchPredictionRequest(BaseModel):
    date: date


class BatchPredictionItem(BaseModel):
    country: str
    lat: float
    lon: float
    status: str
    error: str | None = None
    prediction: PredictResponse | None = None


class BatchPredictionResponse(BaseModel):
    date: date
    scope: str
    compute_mode: str
    total: int
    completed: int
    failed: int
    high: int
    medium: int
    low: int
    results: list[BatchPredictionItem]


class ValidationScenarioResponse(BaseModel):
    key: str
    title: str
    source: dict
    event_date: date
    note: str
    ground_truth_hotspots: list[HotspotOut]
    model_hotspots: list[HotspotOut]
    validation_hotspots: list[HotspotOut] = []
    validation_audit: dict[str, str | int | float | bool | dict | list | None] = {}
    prediction: PredictResponse


class ForecastRequest(BaseModel):
    country: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ForecastDay(BaseModel):
    date: date
    flood_likelihood: float
    risk_level: str
    precipitation_mm: float
    soil_moisture: float | None = None
    river_discharge: float | None = None
    warning: bool = False
    data_source: str = "open_meteo"
    forecast_status: str = "ok"
    status_note: str | None = None
    river_discharge_status: str | None = None


class EventOut(BaseModel):
    id: int
    country: str
    event_date: date
    flood_probability: float
    risk_level: str
    classification: str
    source: str

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: int
    country: str
    message: str
    risk_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RegionOut(BaseModel):
    id: int
    country: str
    lat: float
    lon: float
    buffer_km: float
    risk_level: str | None = None
    risk_baseline: float

    model_config = {"from_attributes": True}
