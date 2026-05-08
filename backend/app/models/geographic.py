"""
Geographic areas and monitoring stations models.
Uses PostGIS for spatial data storage and queries.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from ..database import Base


class GeographicArea(Base):
    """Geographic areas for flood monitoring (regions, districts, etc.)."""
    __tablename__ = "geographic_areas"

    area_id = Column(Integer, primary_key=True, index=True)
    area_name = Column(String(120), nullable=False)
    area_type = Column(String(50), nullable=False)  # e.g., 'region', 'district', 'basin'
    geometry_wkt = Column(Geometry('POLYGON', srid=4326), nullable=True)  # WKT polygon
    min_lat = Column(Numeric(9, 6), nullable=True)
    min_lon = Column(Numeric(9, 6), nullable=True)
    max_lat = Column(Numeric(9, 6), nullable=True)
    max_lon = Column(Numeric(9, 6), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stations = relationship("Station", back_populates="area")
    flood_events = relationship("FloodEvent", back_populates="area")
    alert_rules = relationship("AlertRule", back_populates="area")
    subscriptions = relationship("UserAreaSubscription", back_populates="area", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GeographicArea(area_id={self.area_id}, name='{self.area_name}', type='{self.area_type}')>"


class Station(Base):
    """Monitoring stations within geographic areas."""
    __tablename__ = "stations"

    station_id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, ForeignKey("geographic_areas.area_id"), nullable=False)
    station_code = Column(String(50), unique=True, nullable=False, index=True)
    station_name = Column(String(120), nullable=False)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    elevation_m = Column(Numeric(10, 2), nullable=True)
    status = Column(String(30), default='ACTIVE')  # ACTIVE, INACTIVE, MAINTENANCE
    installed_at = Column(DateTime(timezone=True), nullable=True)

    area = relationship("GeographicArea", back_populates="stations")
    sensors = relationship("Sensor", back_populates="station")
    measurements = relationship("Measurement", back_populates="station")
    alerts = relationship("Alert", back_populates="station")
    alert_rules = relationship("AlertRule", back_populates="station")

    def __repr__(self):
        return f"<Station(station_id={self.station_id}, code='{self.station_code}', name='{self.station_name}')>"