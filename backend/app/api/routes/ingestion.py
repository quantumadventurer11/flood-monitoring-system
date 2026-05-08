"""
Satellite data ingestion and pipeline management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ...database import get_db
from ...models.ingestion import DataSource, IngestJob, IngestError
from ...services.satellite import fetch_sentinel_data

router = APIRouter()


@router.get("/sources")
def list_data_sources(db: Session = Depends(get_db)):
    """List all configured data sources."""
    return db.query(DataSource).filter(DataSource.is_active == True).all()


@router.get("/jobs")
def list_ingest_jobs(
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """List recent ingestion jobs."""
    from sqlalchemy import desc
    query = db.query(IngestJob)
    if status:
        query = query.filter(IngestJob.status == status)
    return query.order_by(desc(IngestJob.started_at)).limit(limit).all()


@router.post("/trigger/sentinel")
def trigger_sentinel_ingestion(
    background_tasks: BackgroundTasks,
    area_id: int = Query(..., description="Geographic area ID to fetch data for"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    satellite: str = Query("S1", description="S1 for Sentinel-1, S2 for Sentinel-2"),
    db: Session = Depends(get_db)
):
    """
    Trigger a satellite data ingestion job for a specific area and date range.
    Runs in the background using Copernicus STAC API (free).
    """
    # Create job record
    job = IngestJob(
        data_source_id=1,  # Copernicus source
        job_type=f"DOWNLOAD_{satellite}",
        status="PENDING",
        parameters_json=f'{{"area_id": {area_id}, "start_date": "{start_date}", "end_date": "{end_date}", "satellite": "{satellite}"}}'
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Run data fetch in background
    background_tasks.add_task(
        fetch_sentinel_data,
        job_id=job.ingest_job_id,
        area_id=area_id,
        start_date=start_date,
        end_date=end_date,
        satellite=satellite
    )

    return {
        "status": "Job submitted",
        "job_id": job.ingest_job_id,
        "message": f"Fetching {satellite} data for area {area_id} from {start_date} to {end_date}"
    }


@router.get("/jobs/{job_id}/status")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get the status of an ingestion job."""
    job = db.query(IngestJob).filter(IngestJob.ingest_job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    errors = db.query(IngestError).filter(IngestError.ingest_job_id == job_id).all()
    return {
        "job_id": job.ingest_job_id,
        "status": job.status,
        "job_type": job.job_type,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "output_location": job.output_location,
        "errors": [{"code": e.error_code, "message": e.error_message} for e in errors]
    }
