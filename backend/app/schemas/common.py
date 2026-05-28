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


class PredictResponse(BaseModel):
    flood_probability: float
    risk_level: str
    classification: str
    confidence: float


class ForecastRequest(BaseModel):
    country: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ForecastDay(BaseModel):
    date: date
    flood_likelihood: float
    risk_level: str
    precipitation_mm: float
    soil_moisture: float


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
    risk_level: str

    model_config = {"from_attributes": True}
