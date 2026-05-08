"""
Sensor and measurement data API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from ...database import get_db
from ...models.sensors import SensorType, Sensor, Measurement
from ...models.geographic import Station
from ...schemas.sensors import (
    SensorTypeCreate, SensorTypeResponse,
    SensorCreate, SensorResponse,
    MeasurementCreate, MeasurementResponse
)

router = APIRouter()


# ─── SENSOR TYPES ──────────────────────────────────────────────────────────────

@router.get("/types", response_model=List[SensorTypeResponse])
def list_sensor_types(db: Session = Depends(get_db)):
    """List all available sensor types."""
    return db.query(SensorType).all()


@router.post("/types", response_model=SensorTypeResponse, status_code=status.HTTP_201_CREATED)
def create_sensor_type(type_in: SensorTypeCreate, db: Session = Depends(get_db)):
    """Create a new sensor type."""
    existing = db.query(SensorType).filter(SensorType.type_name == type_in.type_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Sensor type already exists")
    sensor_type = SensorType(**type_in.model_dump())
    db.add(sensor_type)
    db.commit()
    db.refresh(sensor_type)
    return sensor_type


# ─── SENSORS ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[SensorResponse])
def list_sensors(
    station_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all sensors with optional filtering."""
    query = db.query(Sensor)
    if station_id:
        query = query.filter(Sensor.station_id == station_id)
    if status:
        query = query.filter(Sensor.status == status)
    return query.all()


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """Get a specific sensor."""
    sensor = db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor


@router.post("/", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
def create_sensor(sensor_in: SensorCreate, db: Session = Depends(get_db)):
    """Create a new sensor at a station."""
    station = db.query(Station).filter(Station.station_id == sensor_in.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    sensor = Sensor(**sensor_in.model_dump())
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


# ─── MEASUREMENTS ──────────────────────────────────────────────────────────────

@router.get("/measurements/station/{station_id}", response_model=List[MeasurementResponse])
def get_station_measurements(
    station_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get recent measurements for a station."""
    query = db.query(Measurement).filter(Measurement.station_id == station_id)
    if start_time:
        query = query.filter(Measurement.observed_at >= start_time)
    if end_time:
        query = query.filter(Measurement.observed_at <= end_time)
    return query.order_by(desc(Measurement.observed_at)).limit(limit).all()


@router.post("/measurements", response_model=MeasurementResponse, status_code=status.HTTP_201_CREATED)
def create_measurement(m_in: MeasurementCreate, db: Session = Depends(get_db)):
    """Ingest a new sensor measurement."""
    measurement = Measurement(**m_in.model_dump())
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.post("/measurements/bulk", status_code=status.HTTP_201_CREATED)
def bulk_create_measurements(measurements: List[MeasurementCreate], db: Session = Depends(get_db)):
    """Bulk ingest sensor measurements."""
    objs = [Measurement(**m.model_dump()) for m in measurements]
    db.bulk_save_objects(objs)
    db.commit()
    return {"inserted": len(objs), "status": "success"}
