"""
Sensor and measurement models for monitoring data.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class SensorType(Base):
    """Types of sensors (water level, rainfall, temperature, etc.)."""
    __tablename__ = "sensor_types"

    sensor_type_id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(80), unique=True, nullable=False)
    unit = Column(String(32), nullable=True)  # e.g., 'm', 'mm', '°C'
    description = Column(String(255), nullable=True)

    sensors = relationship("Sensor", back_populates="sensor_type")

    def __repr__(self):
        return f"<SensorType(type_name='{self.type_name}', unit='{self.unit}')>"


class Sensor(Base):
    """Individual sensors installed at stations."""
    __tablename__ = "sensors"

    sensor_id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False)
    sensor_type_id = Column(Integer, ForeignKey("sensor_types.sensor_type_id"), nullable=False)
    serial_number = Column(String(80), nullable=True)
    status = Column(String(30), default='ACTIVE')  # ACTIVE, INACTIVE, MAINTENANCE
    installed_at = Column(DateTime(timezone=True), nullable=True)
    last_calibration_at = Column(DateTime(timezone=True), nullable=True)

    station = relationship("Station", back_populates="sensors")
    sensor_type = relationship("SensorType", back_populates="sensors")
    measurements = relationship("Measurement", back_populates="sensor")

    def __repr__(self):
        return f"<Sensor(sensor_id={self.sensor_id}, serial='{self.serial_number}')>"


class Measurement(Base):
    """Individual sensor measurements (time series data)."""
    __tablename__ = "measurements"

    measurement_id = Column(BigInteger, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False)
    sensor_id = Column(Integer, ForeignKey("sensors.sensor_id"), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Numeric(18, 6), nullable=False)
    unit = Column(String(32), nullable=True)
    quality_flag = Column(String(20), nullable=True)  # VALID, SUSPECT, INVALID
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    station = relationship("Station", back_populates="measurements")
    sensor = relationship("Sensor", back_populates="measurements")

    def __repr__(self):
        return f"<Measurement(measurement_id={self.measurement_id}, value={self.value}, observed_at='{self.observed_at}')>"