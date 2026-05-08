"""
Geographic areas and monitoring stations API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database import get_db
from ...models.geographic import GeographicArea, Station
from ...schemas.geographic import (
    GeographicAreaCreate, GeographicAreaResponse,
    StationCreate, StationResponse, GeographicAreaWithStations
)

router = APIRouter()


# ─── GEOGRAPHIC AREAS ─────────────────────────────────────────────────────────

@router.get("/areas", response_model=List[GeographicAreaResponse])
def list_areas(
    area_type: Optional[str] = Query(None, description="Filter by area type"),
    db: Session = Depends(get_db)
):
    """List all geographic monitoring areas."""
    query = db.query(GeographicArea)
    if area_type:
        query = query.filter(GeographicArea.area_type == area_type)
    return query.all()


@router.get("/areas/{area_id}", response_model=GeographicAreaWithStations)
def get_area(area_id: int, db: Session = Depends(get_db)):
    """Get a specific geographic area with its stations."""
    area = db.query(GeographicArea).filter(GeographicArea.area_id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Geographic area not found")
    return area


@router.post("/areas", response_model=GeographicAreaResponse, status_code=status.HTTP_201_CREATED)
def create_area(area_in: GeographicAreaCreate, db: Session = Depends(get_db)):
    """Create a new geographic monitoring area."""
    area = GeographicArea(**area_in.model_dump())
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@router.get("/areas/search/bbox", response_model=List[GeographicAreaResponse])
def search_areas_by_bbox(
    min_lat: float = Query(..., description="Minimum latitude"),
    min_lon: float = Query(..., description="Minimum longitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    max_lon: float = Query(..., description="Maximum longitude"),
    db: Session = Depends(get_db)
):
    """Search geographic areas that overlap with a bounding box."""
    areas = db.query(GeographicArea).filter(
        GeographicArea.max_lat >= min_lat,
        GeographicArea.min_lat <= max_lat,
        GeographicArea.max_lon >= min_lon,
        GeographicArea.min_lon <= max_lon
    ).all()
    return areas


# ─── STATIONS ─────────────────────────────────────────────────────────────────

@router.get("/stations", response_model=List[StationResponse])
def list_stations(
    area_id: Optional[int] = Query(None, description="Filter by area ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """List all monitoring stations."""
    query = db.query(Station)
    if area_id:
        query = query.filter(Station.area_id == area_id)
    if status:
        query = query.filter(Station.status == status)
    return query.all()


@router.get("/stations/{station_id}", response_model=StationResponse)
def get_station(station_id: int, db: Session = Depends(get_db)):
    """Get a specific monitoring station."""
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station


@router.post("/stations", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
def create_station(station_in: StationCreate, db: Session = Depends(get_db)):
    """Create a new monitoring station."""
    # Verify area exists
    area = db.query(GeographicArea).filter(GeographicArea.area_id == station_in.area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Geographic area not found")

    station = Station(**station_in.model_dump())
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


@router.get("/stations/geojson/all")
def stations_geojson(db: Session = Depends(get_db)):
    """Return all stations as GeoJSON FeatureCollection for map rendering."""
    stations = db.query(Station).filter(Station.status == "ACTIVE").all()
    features = []
    for s in stations:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(s.longitude), float(s.latitude)]
            },
            "properties": {
                "station_id": s.station_id,
                "station_code": s.station_code,
                "station_name": s.station_name,
                "area_id": s.area_id,
                "status": s.status,
                "elevation_m": float(s.elevation_m) if s.elevation_m else None
            }
        })
    return {
        "type": "FeatureCollection",
        "features": features
    }
