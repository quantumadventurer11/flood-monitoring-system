"""
Satellite data ingestion service.
Fetches Sentinel-1 and Sentinel-2 data from Copernicus STAC API (free).
"""
import requests
import time
import json
from datetime import datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)

CDSE_STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac"
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

SENTINEL_COLLECTIONS = {
    "S1": "SENTINEL-1",
    "S2": "SENTINEL-2"
}


def get_cdse_token(client_id: str, client_secret: str) -> Optional[str]:
    """Obtain an OAuth2 access token from Copernicus Data Space."""
    try:
        response = requests.post(
            CDSE_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        logger.error(f"Failed to get CDSE token: {e}")
        return None


def search_stac_items(
    collection: str,
    bbox: list,
    start_date: str,
    end_date: str,
    limit: int = 10,
    token: Optional[str] = None
) -> list:
    """
    Search the Copernicus STAC API for satellite imagery.
    
    Args:
        collection: STAC collection name (SENTINEL-1, SENTINEL-2)
        bbox: [min_lon, min_lat, max_lon, max_lat]
        start_date: ISO date string (YYYY-MM-DD)
        end_date: ISO date string (YYYY-MM-DD)
        limit: Max results to return
        token: Optional OAuth token
    
    Returns:
        List of STAC feature items
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    search_url = f"{CDSE_STAC_URL}/search"
    payload = {
        "collections": [collection],
        "bbox": bbox,
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "limit": limit
    }

    # Add filters for Sentinel-1
    if "SENTINEL-1" in collection:
        payload["filter"] = {
            "op": "and",
            "args": [
                {"op": "=", "args": [{"property": "productType"}, "GRD"]},
                {"op": "=", "args": [{"property": "operationalMode"}, "IW"]}
            ]
        }

    try:
        response = requests.post(search_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("features", [])
    except requests.exceptions.HTTPError as e:
        logger.warning(f"STAC search HTTP error: {e} - Response: {e.response.text if e.response else 'N/A'}")
        return []
    except Exception as e:
        logger.error(f"STAC search failed: {e}")
        return []


def get_area_bbox(area_id: int) -> Optional[list]:
    """
    Get the bounding box for a geographic area from the database.
    Returns [min_lon, min_lat, max_lon, max_lat] format for STAC.
    """
    from ..database import SessionLocal
    from ..models.geographic import GeographicArea

    db = SessionLocal()
    try:
        area = db.query(GeographicArea).filter(GeographicArea.area_id == area_id).first()
        if not area or not all([area.min_lat, area.min_lon, area.max_lat, area.max_lon]):
            return None
        return [float(area.min_lon), float(area.min_lat), float(area.max_lon), float(area.max_lat)]
    finally:
        db.close()


def update_job_status(job_id: int, status: str, output_location: Optional[str] = None):
    """Update the status of an ingestion job in the database."""
    from ..database import SessionLocal
    from ..models.ingestion import IngestJob

    db = SessionLocal()
    try:
        job = db.query(IngestJob).filter(IngestJob.ingest_job_id == job_id).first()
        if job:
            job.status = status
            if status in ("COMPLETED", "FAILED"):
                job.completed_at = datetime.now(timezone.utc)
            if output_location:
                job.output_location = output_location
            db.commit()
    finally:
        db.close()


def log_job_error(job_id: int, error_code: str, error_message: str):
    """Log an error for an ingestion job."""
    from ..database import SessionLocal
    from ..models.ingestion import IngestError

    db = SessionLocal()
    try:
        error = IngestError(
            ingest_job_id=job_id,
            error_code=error_code,
            error_message=error_message
        )
        db.add(error)
        db.commit()
    finally:
        db.close()


async def fetch_sentinel_data(
    job_id: int,
    area_id: int,
    start_date: str,
    end_date: str,
    satellite: str = "S1"
):
    """
    Background task: fetch Sentinel satellite data catalog items for an area.
    
    This uses the free Copernicus STAC API to discover available imagery
    and store metadata in the database for downstream ML processing.
    """
    logger.info(f"Starting {satellite} data fetch for area {area_id} [{start_date} to {end_date}]")
    update_job_status(job_id, "RUNNING")

    try:
        # Get area bounding box
        bbox = get_area_bbox(area_id)
        if not bbox:
            log_job_error(job_id, "NO_BBOX", f"Area {area_id} has no bounding box defined")
            update_job_status(job_id, "FAILED")
            return

        # Get STAC collection name
        collection = SENTINEL_COLLECTIONS.get(satellite)
        if not collection:
            log_job_error(job_id, "INVALID_SATELLITE", f"Unknown satellite: {satellite}")
            update_job_status(job_id, "FAILED")
            return

        # Search STAC catalog (no auth needed for public catalog search)
        items = search_stac_items(
            collection=collection,
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            limit=20
        )

        if not items:
            logger.warning(f"No {satellite} items found for area {area_id}")
            update_job_status(job_id, "COMPLETED", output_location="no_data")
            return

        # Store catalog metadata as model inputs
        from ..database import SessionLocal
        from ..models.modeling import ModelRun, ModelInput

        db = SessionLocal()
        try:
            # Create a placeholder model run for this data collection
            model_run = ModelRun(
                model_name=f"data_collection_{satellite}",
                model_version="1.0",
                status="PENDING",
                parameters_json=json.dumps({
                    "area_id": area_id,
                    "satellite": satellite,
                    "start_date": start_date,
                    "end_date": end_date,
                    "item_count": len(items)
                })
            )
            db.add(model_run)
            db.flush()

            # Record each found scene as a model input
            for item in items:
                item_id = item.get("id", "unknown")
                datetime_str = item.get("properties", {}).get("datetime", "")
                model_input = ModelInput(
                    model_run_id=model_run.model_run_id,
                    input_type=f"SATELLITE_{satellite}",
                    source_ref=item_id,
                    time_start=datetime.fromisoformat(datetime_str.replace("Z", "+00:00")) if datetime_str else None,
                    input_metadata_json=json.dumps({
                        "stac_item_id": item_id,
                        "collection": collection,
                        "bbox": item.get("bbox"),
                        "properties": item.get("properties", {})
                    })
                )
                db.add(model_input)

            db.commit()
            logger.info(f"Stored {len(items)} catalog items for job {job_id}")
            update_job_status(job_id, "COMPLETED", output_location=f"model_run:{model_run.model_run_id}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Satellite fetch failed for job {job_id}: {e}")
        log_job_error(job_id, "FETCH_ERROR", str(e))
        update_job_status(job_id, "FAILED")
