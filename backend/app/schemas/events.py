"""
Flood event and impact schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class FloodEventResponse(BaseModel):
    """Schema for flood event data in responses."""
    flood_event_id: int
    model_run_id: int
    area_id: int
    detected_at: datetime
    event_start: Optional[datetime] = None
    event_end: Optional[datetime] = None
    confidence: Optional[str] = None
    summary: Optional[str] = None

    class Config:
        from_attributes = True


class EventImpactResponse(BaseModel):
    """Schema for event impact data in responses."""
    impact_id: int
    flood_event_id: int
    impact_type: str
    severity: Optional[str] = None
    estimated_area_sq_km: Optional[Decimal] = None
    estimated_people_affected: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class FloodEventWithImpact(FloodEventResponse):
    """Extended schema including impact data."""
    impacts: list[EventImpactResponse] = []