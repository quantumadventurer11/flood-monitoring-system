from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
import logging

import httpx
import numpy as np
from sqlalchemy.orm import Session

from app.models.entities import Prediction
from app.services.risk import risk_level


logger = logging.getLogger(__name__)
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
FORECAST_CACHE_SECONDS = 1800
_FORECAST_CACHE: dict[tuple[str, float, float], tuple[datetime, list[dict]]] = {}


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

    cache_key = (country.lower(), round(lat, 4), round(lon, 4))
    cached = _FORECAST_CACHE.get(cache_key)
    if cached and (datetime.now(UTC) - cached[0]).total_seconds() < FORECAST_CACHE_SECONDS:
        return [dict(row) for row in cached[1]]

    current_probability = _latest_prediction_probability(db, lat, lon)
    today_rows = [(date.today() + timedelta(days=i)).isoformat() for i in range(5)]
    flood = {}
    river_failed = False
    river_note = "Open-Meteo Flood API river discharge available."
    weather_error = ""
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum",
                "hourly": "soil_moisture_0_to_1cm",
                "forecast_days": 5,
                "timezone": "auto",
            }
            try:
                weather_response = await client.get(FORECAST_URL, params=weather_params)
                weather_response.raise_for_status()
            except Exception as exc:
                logger.warning("Open-Meteo hourly soil forecast failed for %s; retrying daily precipitation only: %s", country, exc)
                weather_params.pop("hourly", None)
                weather_response = await client.get(FORECAST_URL, params=weather_params)
                weather_response.raise_for_status()
            weather = weather_response.json()

        days = weather.get("daily", {}).get("time", [])
        precip = weather.get("daily", {}).get("precipitation_sum", [])
        soil_by_day = _daily_soil_means(weather)
        weather_failed = False
    except Exception as exc:
        logger.warning("Open-Meteo weather forecast failed for %s; returning low-risk fallback: %s", country, exc)
        weather_error = str(exc)
        days = today_rows
        precip = [0.0] * 5
        soil_by_day = {}
        weather_failed = True

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            flood_response = await client.get(
                FLOOD_URL,
                params={"latitude": lat, "longitude": lon, "daily": "river_discharge_mean", "forecast_days": 5},
            )
            flood_response.raise_for_status()
            flood = flood_response.json()
    except Exception as exc:
        logger.warning("Open-Meteo river discharge failed for %s; continuing with weather-only forecast: %s", country, exc)
        river_failed = True
        river_note = "Open-Meteo Flood API river discharge unavailable for this request; forecast uses weather inputs only."

    daily_flood = flood.get("daily", {}) if isinstance(flood, dict) else {}
    discharge_values = daily_flood.get("river_discharge_mean") or daily_flood.get("river_discharge") or []
    discharge_by_day = dict(zip(daily_flood.get("time", []), discharge_values))

    rows: list[dict] = []
    for i in range(5):
        day_str = str(days[i]) if i < len(days) else today_rows[i]
        rain = float(precip[i] or 0.0) if i < len(precip) else 0.0
        soil = float(soil_by_day[day_str]) if day_str in soil_by_day else None
        discharge = discharge_by_day.get(day_str)
        if weather_failed:
            likelihood = 0.1
        else:
            soil_component = _normalize(soil, 0, 0.5) if soil is not None else 0.0
            likelihood = 0.5 * _normalize(rain, 0, 100) + 0.3 * soil_component + 0.2 * current_probability
        forecast_status = "fallback" if weather_failed else "weather_only" if river_failed else "ok"
        status_note = (
            f"Open-Meteo weather forecast failed; using conservative fallback rows. {weather_error}".strip()
            if weather_failed
            else river_note
        )
        rows.append(
            {
                "date": datetime.fromisoformat(day_str).date(),
                "flood_likelihood": round(float(np.clip(likelihood, 0.0, 1.0)), 4),
                "risk_level": risk_level(float(likelihood)),
                "precipitation_mm": round(rain, 2),
                "soil_moisture": round(soil, 3) if soil is not None else None,
                "river_discharge": round(float(discharge), 2) if discharge is not None else None,
                "warning": weather_failed or river_failed,
                "data_source": "fallback" if weather_failed else "open_meteo_weather",
                "forecast_status": forecast_status,
                "status_note": status_note,
                "river_discharge_status": "unavailable" if river_failed else "available" if discharge is not None else "missing_for_day",
            }
        )
    if not weather_failed:
        _FORECAST_CACHE[cache_key] = (datetime.now(UTC), [dict(row) for row in rows])
    elif cached:
        stale_rows = [dict(row) for row in cached[1]]
        for row in stale_rows:
            row["forecast_status"] = "cached"
            row["warning"] = True
            row["status_note"] = f"Open-Meteo weather forecast failed; showing cached forecast from {cached[0].isoformat()} UTC."
        return stale_rows
    return rows
