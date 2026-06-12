import asyncio
import math
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Prediction, Region
from app.schemas import BatchPredictionRequest, BatchPredictionResponse, PredictRequest, PredictResponse
from app.services.classifier import predict
from app.services.preprocessing import preprocess_scene
from app.services.satellite import fetch_satellite_scene

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictResponse)
async def run_prediction(payload: PredictRequest, db: Session = Depends(get_db)) -> dict:
    """Fetch satellite data, preprocess the center patch, and classify flood risk."""

    response = await compute_prediction(payload)
    persist_prediction(db, payload, response)
    return response


@router.post("/batch/regions", response_model=BatchPredictionResponse)
async def run_region_batch(payload: BatchPredictionRequest, db: Session = Depends(get_db)) -> dict:
    """Run the model across all configured monitoring regions with bounded concurrency."""

    regions = db.query(Region).order_by(Region.country.asc()).all()
    semaphore = asyncio.Semaphore(10)

    async def compute_region(region: Region) -> dict:
        request = PredictRequest(country=region.country, lat=region.lat, lon=region.lon, date=payload.date)
        async with semaphore:
            try:
                prediction = await asyncio.wait_for(compute_prediction(request), timeout=18)
                return {
                    "country": region.country,
                    "lat": region.lat,
                    "lon": region.lon,
                    "status": "ok",
                    "prediction": prediction,
                }
            except Exception as exc:  # pragma: no cover - defensive per-region isolation.
                return {
                    "country": region.country,
                    "lat": region.lat,
                    "lon": region.lon,
                    "status": "error",
                    "error": str(exc),
                    "prediction": None,
                }

    results = await asyncio.gather(*(compute_region(region) for region in regions))
    for item in results:
        if item["prediction"]:
            request = PredictRequest(country=item["country"], lat=item["lat"], lon=item["lon"], date=payload.date)
            persist_prediction(db, request, item["prediction"])

    completed = [item for item in results if item["status"] == "ok" and item["prediction"]]
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    for item in completed:
        risk = item["prediction"]["risk_level"]
        if risk in risk_counts:
            risk_counts[risk] += 1

    return {
        "date": payload.date,
        "scope": "seeded_monitoring_regions",
        "compute_mode": "classical_async_bounded_concurrency",
        "total": len(results),
        "completed": len(completed),
        "failed": len(results) - len(completed),
        "high": risk_counts["High"],
        "medium": risk_counts["Medium"],
        "low": risk_counts["Low"],
        "results": results,
    }


async def compute_prediction(payload: PredictRequest) -> dict:
    """Compute a prediction response without writing to the database."""

    scene = await fetch_satellite_scene(
        payload.country,
        payload.lat,
        payload.lon,
        50.0,
        payload.date - timedelta(days=1),
        payload.date,
    )
    patch_probabilities = await asyncio.to_thread(scene_patch_probabilities, scene)
    result = summarize_scene_prediction(patch_probabilities)
    result["hotspots"] = patch_hotspots(patch_probabilities, payload.lat, payload.lon, 50.0)
    data_source = str(scene.get("source", "fallback"))
    if data_source == "fallback":
        result["confidence"] = min(float(result["confidence"]), 0.65)
        result["validation_status"] = "fallback_not_ground_truth_validated"
        result["validation_note"] = (
            "Copernicus/Sentinel credentials are unavailable, so this is an Open-Meteo proxy triage score. "
            "The fallback failed the UNOSAT Bangladesh ground-truth recall audit and must not be cited as a validated flood map."
        )
    else:
        result["validation_status"] = "sentinel_scene_ready_for_unosat_audit"
        result["validation_note"] = "Computed from Sentinel scene data; compare exported patch scores with UNOSAT labels before citing independent metrics."

    satellite_date = date.fromisoformat(str(scene.get("date", payload.date.isoformat()))[:10])
    return {
        **result,
        "data_source": data_source,
        "date": satellite_date,
        "rain_7d_mm": scene.get("rain_7d_mm"),
        "max_daily_rain_mm": scene.get("max_daily_rain_mm"),
        "water_signal": scene.get("water_signal"),
    }


def scene_patch_probabilities(scene: dict) -> list[float]:
    patches = preprocess_scene(scene)
    if not patches:
        raise HTTPException(status_code=422, detail="No 64x64 patches could be extracted from the scene")
    patch_results = [predict(patch["features"]) for patch in patches]
    return [float(result["flood_probability"]) for result in patch_results]


def persist_prediction(db: Session, payload: PredictRequest, response: dict) -> None:
    """Store a prediction audit row."""

    satellite_date = date.fromisoformat(str(response.get("date", payload.date.isoformat()))[:10])
    db.add(
        Prediction(
            country=payload.country,
            lat=payload.lat,
            lon=payload.lon,
            target_date=payload.date,
            flood_probability=float(response["flood_probability"]),
            risk_level=str(response["risk_level"]),
            classification=str(response["classification"]),
            confidence=float(response["confidence"]),
            data_source=str(response.get("data_source", "fallback")),
            satellite_date=satellite_date,
        )
    )
    db.commit()


def summarize_scene_prediction(probabilities: list[float]) -> dict[str, float | str]:
    """Aggregate patch probabilities so one wet-looking patch cannot dominate a scene."""

    if not probabilities:
        raise ValueError("At least one probability is required")
    sorted_probabilities = sorted(probabilities)
    flooded_share = sum(probability >= 0.5 for probability in probabilities) / len(probabilities)
    mean_probability = sum(probabilities) / len(probabilities)
    median_probability = sorted_probabilities[len(sorted_probabilities) // 2]
    scene_probability = max(mean_probability * 0.7 + flooded_share * 0.3, median_probability * 0.8)
    scene_probability = max(0.0, min(1.0, scene_probability))
    if scene_probability < 0.30:
        risk = "Low"
    elif scene_probability <= 0.60:
        risk = "Medium"
    else:
        risk = "High"
    return {
        "flood_probability": round(scene_probability, 4),
        "classification": "flood" if scene_probability >= 0.5 else "no_flood",
        "risk_level": risk,
        "confidence": round(max(scene_probability, 1 - scene_probability), 4),
    }


def patch_hotspots(probabilities: list[float], center_lat: float, center_lon: float, buffer_km: float, limit: int = 5) -> list[dict]:
    """Approximate patch centroids for the highest-probability model outputs."""

    if not probabilities:
        return []
    cols = int(math.sqrt(len(probabilities)))
    rows = math.ceil(len(probabilities) / max(1, cols))
    lat_radius = buffer_km / 111.0
    lon_radius = buffer_km / max(1e-6, 111.0 * math.cos(math.radians(center_lat)))
    min_lat, max_lat = center_lat - lat_radius, center_lat + lat_radius
    min_lon, max_lon = center_lon - lon_radius, center_lon + lon_radius
    lat_step = (max_lat - min_lat) / rows
    lon_step = (max_lon - min_lon) / cols

    hotspots = []
    for index, probability in enumerate(probabilities):
        row = index // cols
        col = index % cols
        lat = max_lat - (row + 0.5) * lat_step
        lon = min_lon + (col + 0.5) * lon_step
        risk = "High" if probability > 0.60 else "Medium" if probability >= 0.30 else "Low"
        hotspots.append(
            {
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "probability": round(float(probability), 4),
                "risk_level": risk,
                "source": "model_patch_probability",
            }
        )
    return sorted(hotspots, key=lambda item: item["probability"], reverse=True)[:limit]
