"""
Sensor and measurement schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class SensorTypeCreate(BaseModel):
    """Schema for creating a sensor type."""
    type_name: str = Field(..., min_length=1, max_length=80)
    unit: Optional[str] = Field(None, max_length=32)
    description: Optional[str] = Field(None, max_length=255)


class SensorTypeResponse(BaseModel):
    """Schema for sensor type data in responses."""
    sensor_type_id: int
    type_name: str
    unit: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SensorCreate(BaseModel):
    """Schema for creating a sensor."""
    station_id: int
    sensor_type_id: int
    serial_number: Optional[str] = Field(None, max_length=80)
    status: Optional[str] = 'ACTIVE'


class SensorResponse(BaseModel):
    """Schema for sensor data in responses."""
    sensor_id: int
    station_id: int
    sensor_type_id: int
    serial_number: Optional[str] = None
    status: str
    installed_at: Optional[datetime] = None
    last_calibration_at: Optional[datetime] = None
    sensor_type: Optional[SensorTypeResponse] = None

    class Config:
        from_attributes = True


class MeasurementCreate(BaseModel):
    """Schema for creating a measurement."""
    station_id: int
    sensor_id: int
    observed_at: datetime
    value: Decimal = Field(..., decimal_places=6)
    unit: Optional[str] = Field(None, max_length=32)
    quality_flag: Optional[str] = None


class MeasurementResponse(BaseModel):
    """Schema for measurement data in responses."""
    measurement_id: int
    station_id: int
    sensor_id: int
    observed_at: datetime
    value: Decimal
    unit: Optional[str] = None
    quality_flag: Optional[str] = None
    ingested_at: datetime

    class Config:
        from_attributes = True


class MeasurementTimeSeries(BaseModel):
    """Schema for time series measurement data."""
    sensor_id: int
    station_id: int
    measurements: list[MeasurementResponse]
    start_time: datetime
    end_time: datetime