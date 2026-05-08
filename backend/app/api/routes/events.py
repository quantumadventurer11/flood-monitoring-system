"""
Flood events API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from ...database import get_db
from ...models.events import FloodEvent, EventImpact
from ...schemas.events import FloodEventResponse, EventImpactResponse, FloodEventWithImpact

router = APIRouter()


@router.get("/", response_model=List[FloodEventResponse])
def list_flood_events(
    area_id: Optional[int] = Query(None),
    confidence: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    """List flood events with optional filtering."""
    query = db.query(FloodEvent)
    if area_id:
        query = query.filter(FloodEvent.area_id == area_id)
    if confidence:
        query = query.filter(FloodEvent.confidence == confidence)
    if start_date:
        query = query.filter(FloodEvent.detected_at >= start_date)
    if end_date:
        query = query.filter(FloodEvent.detected_at <= end_date)
    return query.order_by(desc(FloodEvent.detected_at)).limit(limit).all()


@router.get("/{event_id}", response_model=FloodEventWithImpact)
def get_flood_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific flood event with impact data."""
    event = db.query(FloodEvent).filter(FloodEvent.flood_event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Flood event not found")
    return event


@router.get("/area/{area_id}/recent")
def get_recent_area_events(
    area_id: int,
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db)
):
    """Get the most recent flood events for a specific area."""
    events = db.query(FloodEvent).filter(
        FloodEvent.area_id == area_id
    ).order_by(desc(FloodEvent.detected_at)).limit(limit).all()
    return events


@router.get("/summary/global")
def global_flood_summary(db: Session = Depends(get_db)):
    """Get a summary of current global flood events for the dashboard."""
    from sqlalchemy import func
    total = db.query(func.count(FloodEvent.flood_event_id)).scalar()
    high_confidence = db.query(func.count(FloodEvent.flood_event_id)).filter(
        FloodEvent.confidence == "HIGH"
    ).scalar()
    return {
        "total_events": total,
        "high_confidence_events": high_confidence,
        "medium_confidence_events": db.query(func.count(FloodEvent.flood_event_id)).filter(
            FloodEvent.confidence == "MEDIUM"
        ).scalar(),
        "recent_events": db.query(FloodEvent).order_by(
            desc(FloodEvent.detected_at)
        ).limit(5).all()
    }
