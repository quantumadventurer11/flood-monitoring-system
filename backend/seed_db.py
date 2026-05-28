from datetime import date

from app.database import SessionLocal, init_db
from app.models.entities import Alert, Event, PaperResult, Region
from app.services.paper_data import PAPER_RESULTS


GLOBAL_REGIONS = [
    ("Bangladesh", 23.685, 90.3563, 0.82),
    ("India", 20.5937, 78.9629, 0.68),
    ("Pakistan", 30.3753, 69.3451, 0.64),
    ("Nigeria", 9.082, 8.6753, 0.61),
    ("Mozambique", -18.6657, 35.5296, 0.66),
    ("Indonesia", -0.7893, 113.9213, 0.65),
    ("Philippines", 12.8797, 121.774, 0.63),
    ("Vietnam", 14.0583, 108.2772, 0.70),
    ("China", 35.8617, 104.1954, 0.58),
    ("Brazil", -14.235, -51.9253, 0.57),
    ("Peru", -9.19, -75.0152, 0.49),
    ("USA", 37.0902, -95.7129, 0.42),
    ("Canada", 56.1304, -106.3468, 0.35),
    ("Germany", 51.1657, 10.4515, 0.39),
    ("Netherlands", 52.1326, 5.2913, 0.62),
    ("Australia", -25.2744, 133.7751, 0.45),
    ("Japan", 36.2048, 138.2529, 0.52),
    ("Myanmar", 21.9162, 95.956, 0.67),
    ("Thailand", 15.87, 100.9925, 0.58),
    ("Cambodia", 12.5657, 104.991, 0.55),
    ("South Sudan", 6.877, 31.307, 0.72),
    ("Somalia", 5.1521, 46.1996, 0.50),
    ("Ethiopia", 9.145, 40.4897, 0.47),
    ("Ghana", 7.9465, -1.0232, 0.46),
    ("Mexico", 23.6345, -102.5528, 0.44),
    ("Colombia", 4.5709, -74.2973, 0.53),
    ("Bolivia", -16.2902, -63.5887, 0.48),
]


def _risk_from_baseline(value: float) -> str:
    if value < 0.3:
        return "Low"
    if value <= 0.6:
        return "Medium"
    return "High"


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

        for country, lat, lon, baseline in GLOBAL_REGIONS:
            row = db.query(Region).filter(Region.country == country).one_or_none()
            if row:
                row.lat = lat
                row.lon = lon
                row.risk_baseline = baseline
                row.risk_level = _risk_from_baseline(baseline)
            else:
                db.add(Region(country=country, lat=lat, lon=lon, buffer_km=50, risk_level=_risk_from_baseline(baseline), risk_baseline=baseline))

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
