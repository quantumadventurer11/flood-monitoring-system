from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Prediction
from app.schemas import PredictRequest, PredictResponse
from app.services.classifier import predict
from app.services.preprocessing import preprocess_scene
from app.services.satellite import fetch_satellite_scene

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictResponse)
async def run_prediction(payload: PredictRequest, db: Session = Depends(get_db)) -> dict:
    """Fetch satellite data, preprocess the center patch, and classify flood risk."""

    scene = await fetch_satellite_scene(
        payload.country,
        payload.lat,
        payload.lon,
        50.0,
        payload.date - timedelta(days=1),
        payload.date,
    )
    patches = preprocess_scene(scene)
    if not patches:
        raise HTTPException(status_code=422, detail="No 64x64 patches could be extracted from the scene")
    center_patch = patches[len(patches) // 2]
    result = predict(center_patch["features"])
    satellite_date = date.fromisoformat(str(scene.get("date", payload.date.isoformat()))[:10])
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
            data_source=str(scene.get("source", "fallback")),
            satellite_date=satellite_date,
        )
    )
    db.commit()
    return {**result, "data_source": str(scene.get("source", "fallback")), "date": satellite_date}
