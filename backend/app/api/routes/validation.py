from datetime import date

from fastapi import APIRouter

from app.schemas import ValidationScenarioResponse
from app.services.independent_validation import (
    UNOSAT_BANGLADESH_2024,
    PatchLabel,
)

router = APIRouter(prefix="/validation/scenarios", tags=["validation"])


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
        "prediction": prediction,
    }


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
