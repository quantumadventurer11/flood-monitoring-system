from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ForecastDay, ForecastRequest
from app.services.forecaster import fetch_forecast

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("", response_model=list[ForecastDay])
async def run_forecast(payload: ForecastRequest, db: Session = Depends(get_db)) -> list[dict]:
    """Return a five-day operational flood forecast from Open-Meteo weather data."""

    return await fetch_forecast(payload.country, payload.lat, payload.lon, db)
