import csv
from datetime import date
from pathlib import Path

from fastapi import APIRouter

from app.schemas import ValidationScenarioResponse
from app.services.cross_region_validation import build_cross_region_report
from app.services.independent_validation import (
    UNOSAT_BANGLADESH_2024,
    PatchLabel,
)

router = APIRouter(prefix="/validation/scenarios", tags=["validation"])
ROOT = Path(__file__).resolve().parents[3]
BANGLADESH_AUDIT_CSV = ROOT / "validation" / "audits" / "bangladesh_2024" / "patch_level_audit.csv"


@router.get("/bangladesh-2024", response_model=ValidationScenarioResponse)
async def bangladesh_2024_scenario() -> dict:
    """Return a known UNOSAT flood scenario using only local derived data."""

    event_date = date(2024, 9, 4)
    labels = _unosat_labels()
    flooded_labels = [label for label in labels if label.label == 1]
    ground_truth_hotspots = [
        {
            "lat": round(label.lat, 6),
            "lon": round(label.lon, 6),
            "probability": 1.0,
            "risk_level": "Ground truth flood",
            "source": "UNOSAT_FL20240825BGD_patch_label",
            "flood_class": "Satellite-detected flood extent",
            "details": {
                "event_code": UNOSAT_BANGLADESH_2024["event_code"],
                "sensor": UNOSAT_BANGLADESH_2024["sensor"],
                "acquisition_window": UNOSAT_BANGLADESH_2024["acquisition_window"],
                "patch_id": label.patch_id,
                "class_basis": "Patch centroid is inside the locally derived UNOSAT flood extent label set.",
                "validation_type": "Ground truth flood coordinate",
            },
            "data": {
                "latitude": round(label.lat, 6),
                "longitude": round(label.lon, 6),
                "label": label.label,
                "reported_flooded_area_km2": UNOSAT_BANGLADESH_2024["reported_flooded_area_km2"],
                "reported_receded_area_km2": UNOSAT_BANGLADESH_2024["reported_receded_area_km2"],
                "reported_exposed_population": UNOSAT_BANGLADESH_2024["reported_exposed_population"],
                "source_product_id": UNOSAT_BANGLADESH_2024["product_id"],
            },
        }
        for label in flooded_labels[:12]
    ]
    prediction = {
        "flood_probability": 1.0,
        "risk_level": "High",
        "classification": "flood",
        "confidence": 1.0,
        "data_source": "local_unosat_ground_truth",
        "date": event_date,
        "operational_mode": "local_ground_truth_coordinate_scenario",
        "publishable": True,
        "validation_status": "ground_truth_coordinate_scenario",
        "validation_note": "Bangladesh 2024 scenario uses only locally stored UNOSAT-derived flood patch coordinates; no internet data is fetched for these flood-point records.",
        "rain_7d_mm": None,
        "max_daily_rain_mm": None,
        "water_signal": None,
        "hotspots": ground_truth_hotspots,
    }
    validation_hotspots, validation_audit = _validation_audit_markers()

    return {
        "key": "bangladesh_2024_unosat",
        "title": "Bangladesh 2024 flood, UNOSAT FL20240825BGD",
        "source": UNOSAT_BANGLADESH_2024,
        "event_date": event_date,
        "note": (
            "Markers come from locally stored UNOSAT Sentinel-1 flood-extent patch labels. "
            "Each coordinate includes its own class, source details, and data fields from the local validation dataset."
        ),
        "ground_truth_hotspots": ground_truth_hotspots,
        "model_hotspots": [],
        "validation_hotspots": validation_hotspots,
        "validation_audit": validation_audit,
        "prediction": prediction,
    }


@router.get("/cross-region")
async def cross_region_validation() -> dict:
    """Return cross-region validation readiness, real metrics when supplied, and app health."""

    return build_cross_region_report()


def _unosat_labels() -> list[PatchLabel]:
    unosat_derived_centroids = [
        (92.315332, 25.029101),
        (91.001422, 24.840229),
        (89.103553, 24.651357),
        (91.585382, 24.651357),
        (91.877362, 24.651357),
        (88.811573, 24.462485),
        (90.417462, 24.462485),
        (91.877362, 24.462485),
        (90.563452, 24.273613),
        (89.541523, 23.895869),
        (91.147412, 23.895869),
        (91.147412, 23.518125),
    ]
    return [
        PatchLabel(
            f"UNOSAT-2024-derived-{index:02d}",
            lon,
            lat,
            1,
        )
        for index, (lon, lat) in enumerate(unosat_derived_centroids)
    ]


def _validation_audit_markers() -> tuple[list[dict], dict]:
    if not BANGLADESH_AUDIT_CSV.exists():
        return [], {
            "artifact_status": "scores_required",
            "publishable": False,
            "artifact": str(BANGLADESH_AUDIT_CSV.relative_to(ROOT)),
            "note": "Patch-level audit CSV has not been generated yet. Run backend/scripts/validate_unosat_bangladesh.py with real patch scores.",
        }

    markers: list[dict] = []
    counts: dict[str, int] = {}
    with BANGLADESH_AUDIT_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        error_type = row.get("error_type") or "score_missing"
        counts[error_type] = counts.get(error_type, 0) + 1
        if len(markers) >= 24:
            continue
        if error_type == "true_negative":
            continue
        probability_text = row.get("model_probability")
        probability = float(probability_text) if probability_text not in {None, ""} else 0.0
        label = int(float(row.get("unosat_label") or 0))
        markers.append(
            {
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "probability": probability,
                "risk_level": error_type.replace("_", " ").title(),
                "source": "local_patch_level_validation_audit",
                "flood_class": error_type,
                "details": {
                    "patch_id": row.get("patch_id"),
                    "error_type": error_type,
                    "label_source": row.get("label_source"),
                    "score_source": row.get("score_source"),
                    "scene_date": row.get("scene_date"),
                    "validation_type": "UNOSAT label compared with model probability",
                },
                "data": {
                    "unosat_label": label,
                    "ndwi_water_fraction": _optional_float(row.get("ndwi_water_fraction")),
                    "model_probability": _optional_float(row.get("model_probability")),
                    "prediction_class": row.get("prediction_class"),
                },
            }
        )

    return markers, {
        "artifact_status": "computed" if rows and counts.get("score_missing", 0) == 0 else "scores_required",
        "publishable": bool(rows) and counts.get("score_missing", 0) == 0,
        "artifact": str(BANGLADESH_AUDIT_CSV.relative_to(ROOT)),
        "patches": len(rows),
        "error_type_counts": counts,
        "note": "Validation classes use UNOSAT as ground truth and model_probability as prediction; NDWI is a feature column only.",
    }


def _optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)
