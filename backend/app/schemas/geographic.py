"""
Geographic schemas for areas and stations.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class GeographicAreaCreate(BaseModel):
    """Schema for creating a geographic area."""
    area_name: str = Field(..., min_length=1, max_length=120)
    area_type: str = Field(..., min_length=1, max_length=50)  # region, district, basin
    min_lat: Optional[Decimal] = None
    min_lon: Optional[Decimal] = None
    max_lat: Optional[Decimal] = None
    max_lon: Optional[Decimal] = None
    geometry_wkt: Optional[str] = None  # Well-Known Text format for polygon


class GeographicAreaResponse(BaseModel):
    """Schema for geographic area data in responses."""
    area_id: int
    area_name: str
    area_type: str
    min_lat: Optional[Decimal] = None
    min_lon: Optional[Decimal] = None
    max_lat: Optional[Decimal] = None
    max_lon: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StationCreate(BaseModel):
    """Schema for creating a monitoring station."""
    area_id: int
    station_code: str = Field(..., min_length=1, max_length=50)
    station_name: str = Field(..., min_length=1, max_length=120)
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    elevation_m: Optional[Decimal] = None
    status: Optional[str] = 'ACTIVE'


class StationResponse(BaseModel):
    """Schema for station data in responses."""
    station_id: int
    area_id: int
    station_code: str
    station_name: str
    latitude: Decimal
    longitude: Decimal
    elevation_m: Optional[Decimal] = None
    status: str
    installed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GeographicAreaWithStations(GeographicAreaResponse):
    """Extended schema including related stations."""
    stations: list[StationResponse] = []