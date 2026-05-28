from collections import defaultdict
from datetime import date, datetime, timedelta
import logging

import httpx
import numpy as np
from sqlalchemy.orm import Session

from app.models.entities import Prediction
from app.services.risk import risk_level


logger = logging.getLogger(__name__)
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"


def _normalize(value: float | None, lo: float, hi: float) -> float:
    if value is None:
        return 0.0
    return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))


def _latest_prediction_probability(db: Session, lat: float, lon: float) -> float:
    prediction = (
        db.query(Prediction)
        .filter(Prediction.lat.between(lat - 0.5, lat + 0.5), Prediction.lon.between(lon - 0.5, lon + 0.5))
        .order_by(Prediction.created_at.desc())
        .first()
    )
    return float(prediction.flood_probability) if prediction else 0.1


def _daily_soil_means(payload: dict) -> dict[str, float]:
    by_day: dict[str, list[float]] = defaultdict(list)
    times = payload.get("hourly", {}).get("time", [])
    values = payload.get("hourly", {}).get("soil_moisture_0_to_1cm", [])
    for timestamp, value in zip(times, values):
        if value is not None:
            by_day[str(timestamp)[:10]].append(float(value))
    return {day: float(np.mean(items)) for day, items in by_day.items() if items}


async def fetch_forecast(country: str, lat: float, lon: float, db: Session) -> list[dict]:
    """Fetch Open-Meteo weather/flood data and compute five-day flood likelihood."""

    current_probability = _latest_prediction_probability(db, lat, lon)
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            weather_response = await client.get(
                FORECAST_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "precipitation_sum",
                    "hourly": "soil_moisture_0_to_1cm",
                    "forecast_days": 5,
                    "timezone": "auto",
                },
            )
            weather_response.raise_for_status()
            weather = weather_response.json()

            flood_response = await client.get(
                FLOOD_URL,
                params={"latitude": lat, "longitude": lon, "daily": "river_discharge_mean", "forecast_days": 5},
            )
            flood_response.raise_for_status()
            flood = flood_response.json()

        days = weather.get("daily", {}).get("time", [])
        precip = weather.get("daily", {}).get("precipitation_sum", [])
        soil_by_day = _daily_soil_means(weather)
        discharge_by_day = dict(zip(flood.get("daily", {}).get("time", []), flood.get("daily", {}).get("river_discharge_mean", [])))
        failed = False
    except Exception as exc:
        logger.warning("Open-Meteo forecast failed for %s; returning low-risk fallback: %s", country, exc)
        days = [(date.today() + timedelta(days=i)).isoformat() for i in range(5)]
        precip = [0.0] * 5
        soil_by_day = {}
        discharge_by_day = {}
        failed = True

    rows: list[dict] = []
    for i in range(5):
        day_str = str(days[i]) if i < len(days) else (date.today() + timedelta(days=i)).isoformat()
        rain = float(precip[i] or 0.0) if i < len(precip) else 0.0
        soil = float(soil_by_day.get(day_str, 0.0))
        discharge = discharge_by_day.get(day_str)
        if failed:
            likelihood = 0.1
        else:
            likelihood = 0.5 * _normalize(rain, 0, 100) + 0.3 * _normalize(soil, 0, 0.5) + 0.2 * current_probability
        rows.append(
            {
                "date": datetime.fromisoformat(day_str).date(),
                "flood_likelihood": round(float(np.clip(likelihood, 0.0, 1.0)), 4),
                "risk_level": risk_level(float(likelihood)),
                "precipitation_mm": round(rain, 2),
                "soil_moisture": round(soil, 3),
                "river_discharge": round(float(discharge), 2) if discharge is not None else None,
                "warning": failed,
            }
        )
    return rows
