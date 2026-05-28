from datetime import date

from app.database import SessionLocal, init_db
from app.models.entities import Alert, Event, PaperResult, Region
from app.services.paper_data import PAPER_RESULTS


def seed() -> None:
    """Seed paper results and starter operational data idempotently."""

    init_db()
    db = SessionLocal()
    try:
        for key, payload in PAPER_RESULTS.items():
            row = db.query(PaperResult).filter(PaperResult.key == key).one_or_none()
            if row:
                row.payload = payload
            else:
                db.add(PaperResult(key=key, payload=payload))

        if db.query(Region).count() == 0:
            db.add_all(
                [
                    Region(country="Bangladesh", lat=23.8103, lon=90.4125, buffer_km=50, risk_level="High"),
                    Region(country="India", lat=20.5937, lon=78.9629, buffer_km=75, risk_level="Medium"),
                    Region(country="United States", lat=37.0902, lon=-95.7129, buffer_km=100, risk_level="Low"),
                ]
            )

        if db.query(Event).count() == 0:
            db.add_all(
                [
                    Event(country="Bangladesh", event_date=date(2024, 8, 1), flood_probability=0.91, risk_level="High", classification="flood", source="paper-test-set"),
                    Event(country="Bangladesh", event_date=date(2024, 7, 1), flood_probability=0.64, risk_level="Medium", classification="flood", source="paper-training-set"),
                    Event(country="Bangladesh", event_date=date(2024, 6, 1), flood_probability=0.78, risk_level="High", classification="flood", source="paper-training-set"),
                ]
            )

        if db.query(Alert).count() == 0:
            db.add(Alert(country="Bangladesh", risk_level="High", message="Bangladesh: High flood risk detected around the Dhaka 50 km study buffer."))

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
