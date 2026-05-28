from fastapi import APIRouter, HTTPException

from app.schemas import IngestRequest, IngestResponse
from app.services.satellite import ingest_sentinel_scene

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=IngestResponse)
async def ingest(payload: IngestRequest) -> dict:
    """Ingest Sentinel products for a region, falling back to simulated patch metadata."""

    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    return await ingest_sentinel_scene(
        payload.country,
        payload.lat,
        payload.lon,
        payload.buffer_km,
        payload.start_date,
        payload.end_date,
    )
