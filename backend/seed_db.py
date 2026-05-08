"""
Run this script once to seed the database with initial data.
Usage: python seed_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base, init_db
from app.services.seed import seed_database

# Import all models so they are registered with Base
from app.models import (
    auth, geographic, sensors, ingestion,
    modeling, events, alerts, audit
)

if __name__ == "__main__":
    print("Initialising database …")
    init_db()
    Base.metadata.create_all(bind=engine)
    print("Running seed …")
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    print("Done!")
