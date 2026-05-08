"""
Flood event detection and impact assessment models.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class FloodEvent(Base):
    """Detected flood events from satellite analysis or sensor data."""
    __tablename__ = "flood_events"

    flood_event_id = Column(BigInteger, primary_key=True, index=True)
    model_run_id = Column(BigInteger, ForeignKey("model_runs.model_run_id", ondelete="CASCADE"), nullable=False)
    area_id = Column(Integer, ForeignKey("geographic_areas.area_id"), nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    event_start = Column(DateTime(timezone=True), nullable=True)
    event_end = Column(DateTime(timezone=True), nullable=True)
    confidence = Column(String(30), nullable=True)  # LOW, MEDIUM, HIGH
    summary = Column(String(1000), nullable=True)

    model_run = relationship("ModelRun", back_populates="flood_events")
    area = relationship("GeographicArea", back_populates="flood_events")
    impacts = relationship("EventImpact", back_populates="flood_event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FloodEvent(flood_event_id={self.flood_event_id}, area='{self.area_id}', detected_at='{self.detected_at}')>"


class EventImpact(Base):
    """Impact assessment for flood events."""
    __tablename__ = "event_impacts"

    impact_id = Column(BigInteger, primary_key=True, index=True)
    flood_event_id = Column(BigInteger, ForeignKey("flood_events.flood_event_id", ondelete="CASCADE"), nullable=False)
    impact_type = Column(String(50), nullable=False)  # e.g., 'AREA_FLOODED', 'PEOPLE_AFFECTED'
    severity = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    estimated_area_sq_km = Column(Numeric(12, 2), nullable=True)
    estimated_people_affected = Column(Integer, nullable=True)
    notes = Column(String(1000), nullable=True)

    flood_event = relationship("FloodEvent", back_populates="impacts")

    def __repr__(self):
        return f"<EventImpact(impact_id={self.impact_id}, type='{self.impact_type}')>"