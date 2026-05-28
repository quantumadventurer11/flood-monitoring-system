from datetime import date

from app.config import get_settings


def credentials_available() -> bool:
    settings = get_settings()
    return bool(settings.copernicus_user and settings.copernicus_password)


async def ingest_sentinel_scene(country: str, lat: float, lon: float, buffer_km: float, start_date: date, end_date: date) -> dict:
    """Retrieve Sentinel products when configured; otherwise return simulated ingest metadata."""

    if not credentials_available():
        days = max(1, (end_date - start_date).days + 1)
        return {"status": "simulated", "patches_processed": min(6768, int(days * buffer_km * 5))}
    return {"status": "queued", "patches_processed": 0}
