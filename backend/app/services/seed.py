"""
Database seeder for initial data setup.
Populates the database with Copernicus data source, sensor types,
and a set of well-known flood-prone areas worldwide.
"""
import json
from sqlalchemy.orm import Session


INITIAL_AREAS = [
    {"area_name": "Bangladesh – Brahmaputra Basin",  "area_type": "basin",   "min_lat": 23.0, "min_lon": 89.0,  "max_lat": 26.0, "max_lon": 93.0},
    {"area_name": "Bangladesh – Ganges Delta",        "area_type": "delta",   "min_lat": 21.5, "min_lon": 88.0,  "max_lat": 24.0, "max_lon": 92.0},
    {"area_name": "India – Assam (Brahmaputra)",      "area_type": "region",  "min_lat": 24.0, "min_lon": 89.5,  "max_lat": 28.0, "max_lon": 96.0},
    {"area_name": "Pakistan – Indus River Plain",     "area_type": "basin",   "min_lat": 25.0, "min_lon": 67.0,  "max_lat": 35.0, "max_lon": 73.0},
    {"area_name": "Nigeria – Niger Delta",            "area_type": "delta",   "min_lat":  4.0, "min_lon":  5.0,  "max_lat":  6.0, "max_lon":  8.0},
    {"area_name": "Vietnam – Mekong Delta",           "area_type": "delta",   "min_lat":  8.5, "min_lon": 104.5, "max_lat": 11.5, "max_lon": 107.0},
    {"area_name": "Thailand – Chao Phraya Basin",     "area_type": "basin",   "min_lat": 13.0, "min_lon": 99.5,  "max_lat": 16.0, "max_lon": 102.0},
    {"area_name": "Myanmar – Irrawaddy Delta",        "area_type": "delta",   "min_lat": 15.0, "min_lon": 94.0,  "max_lat": 18.0, "max_lon": 97.5},
    {"area_name": "USA – Mississippi River",          "area_type": "basin",   "min_lat": 29.0, "min_lon": -92.0, "max_lat": 35.0, "max_lon": -88.0},
    {"area_name": "Germany – Rhine & Ahr Region",     "area_type": "region",  "min_lat": 49.5, "min_lon":  6.5,  "max_lat": 52.0, "max_lon":  8.5},
    {"area_name": "China – Yangtze River Middle",     "area_type": "basin",   "min_lat": 28.0, "min_lon": 111.0, "max_lat": 32.0, "max_lon": 117.0},
    {"area_name": "Australia – Murray-Darling Basin", "area_type": "basin",   "min_lat":-37.0, "min_lon": 140.0, "max_lat":-28.0, "max_lon": 149.0},
    {"area_name": "Brazil – Amazon Floodplain",       "area_type": "basin",   "min_lat": -5.0, "min_lon": -68.0, "max_lat":  2.0, "max_lon": -50.0},
    {"area_name": "Kerala – Coastal Southwest India", "area_type": "region",  "min_lat":  8.0, "min_lon": 76.0,  "max_lat": 12.0, "max_lon": 78.0},
    {"area_name": "Mozambique – Limpopo Basin",       "area_type": "basin",   "min_lat":-26.0, "min_lon": 31.0,  "max_lat":-21.0, "max_lon": 36.0},
]

SENSOR_TYPES = [
    {"type_name": "Water Level Gauge",     "unit": "m",    "description": "River / lake water level above datum"},
    {"type_name": "Rainfall",              "unit": "mm/h", "description": "Precipitation intensity"},
    {"type_name": "Soil Moisture",         "unit": "%",    "description": "Volumetric water content of topsoil"},
    {"type_name": "Discharge",             "unit": "m³/s", "description": "Volumetric flow rate"},
    {"type_name": "Air Temperature",       "unit": "°C",   "description": "Ambient air temperature at 2 m height"},
    {"type_name": "SAR Backscatter (VV)",  "unit": "dB",   "description": "Sentinel-1 VV polarisation backscatter"},
    {"type_name": "NDWI",                  "unit": None,   "description": "Normalised Difference Water Index (Sentinel-2)"},
    {"type_name": "NDVI",                  "unit": None,   "description": "Normalised Difference Vegetation Index (Sentinel-2)"},
]


def seed_database(db: Session) -> None:
    """Seed database with initial reference data."""
    from ..models.ingestion import DataSource
    from ..models.geographic import GeographicArea, Station
    from ..models.sensors import SensorType
    from ..models.auth import Role

    # ── Roles ─────────────────────────────────────────────────────────────────
    for role_name, desc in [("admin", "Full system access"), ("analyst", "Data analysis and viewing"), ("user", "Basic monitoring access")]:
        from sqlalchemy import select
        existing = db.query(Role).filter(Role.role_name == role_name).first()
        if not existing:
            db.add(Role(role_name=role_name, role_description=desc))

    # ── Copernicus data source ─────────────────────────────────────────────
    existing_source = db.query(DataSource).filter(DataSource.source_name == "Copernicus STAC API").first()
    if not existing_source:
        db.add(DataSource(
            source_name="Copernicus STAC API",
            source_type="SATELLITE",
            provider="European Space Agency",
            endpoint="https://catalogue.dataspace.copernicus.eu/stac",
            auth_method="OAUTH2",
            is_active=True
        ))

    # ── Sensor types ────────────────────────────────────────────────────────
    for st in SENSOR_TYPES:
        existing = db.query(SensorType).filter(SensorType.type_name == st["type_name"]).first()
        if not existing:
            db.add(SensorType(**st))

    # ── Geographic areas ────────────────────────────────────────────────────
    for area_data in INITIAL_AREAS:
        existing = db.query(GeographicArea).filter(GeographicArea.area_name == area_data["area_name"]).first()
        if not existing:
            db.add(GeographicArea(**area_data))

    db.commit()
    print("✅ Database seeded successfully.")
