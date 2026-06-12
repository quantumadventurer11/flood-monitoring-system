from fastapi import APIRouter

from app.schemas import ModelStatusResponse
from app.services.classifier import MODEL_PATH, classifier
from app.services.satellite import credentials_available

router = APIRouter(prefix="/model-status", tags=["model-status"])


@router.get("", response_model=ModelStatusResponse)
def model_status() -> dict:
    """Report whether production is using satellite-backed inference or fallback proxy mode."""

    credentials_configured = credentials_available()
    fallback_active = not credentials_configured
    model_loaded = classifier.model is not None
    return {
        "backend_status": "ok",
        "model_loaded": model_loaded,
        "model_artifact_present": MODEL_PATH.exists(),
        "model_type": "XGBoost binary flood classifier",
        "data_mode": "copernicus_sentinel" if credentials_configured else "fallback_open_meteo_proxy",
        "fallback_active": fallback_active,
        "copernicus_credentials_configured": credentials_configured,
        "publishable_predictions": credentials_configured,
        "validation_status": "sentinel_scene_ready_for_unosat_audit" if credentials_configured else "fallback_not_ground_truth_validated",
        "note": (
            "Copernicus credentials are configured; predictions can attempt Sentinel-backed inference and still require UNOSAT audit before citation."
            if credentials_configured
            else "Copernicus credentials are not configured; predictions use a fallback Open-Meteo proxy and are not publishable validation results."
        ),
    }
