from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Prediction
from app.schemas import PredictRequest, PredictResponse
from app.services.classifier import predict

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictResponse)
def run_prediction(payload: PredictRequest, db: Session = Depends(get_db)) -> dict:
    """Run the XGBoost flood classifier or deterministic fallback for a location/date."""

    result = predict(payload.country, payload.lat, payload.lon, payload.date)
    db.add(
        Prediction(
            country=payload.country,
            lat=payload.lat,
            lon=payload.lon,
            target_date=payload.date,
            flood_probability=float(result["flood_probability"]),
            risk_level=str(result["risk_level"]),
            classification=str(result["classification"]),
            confidence=float(result["confidence"]),
        )
    )
    db.commit()
    return result
