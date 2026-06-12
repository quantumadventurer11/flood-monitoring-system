from datetime import date

import numpy as np
from fastapi.testclient import TestClient

from app.api.routes.predict import patch_hotspots, summarize_scene_prediction
from app.main import app
from app.services.classifier import generate_synthetic_training_data, train
from app.services.independent_validation import PatchLabel, summarize_validation
from app.services.preprocessing import compute_indices, extract_patch_features, label_patch, preprocess_scene
from app.services.satellite import _surface_water_prior
from seed_db import seed


seed()
client = TestClient(app)


def test_paper_results_exact_values():
    data = client.get("/paper-results").json()
    assert data["dataset_stats"][0]["total_patches"] == 2630
    assert data["model_metrics"][0]["model"] == "XGBoost"
    assert data["model_metrics"][0]["f1"] == 0.923
    assert data["independent_validation"]["source"]["event_code"] == "FL20240825BGD"
    assert data["independent_validation"]["ground_truth"]["flooded_percent"] == 3.12
    assert data["metric_audit"][0]["item"] == "SVM (RBF) ROC-AUC"
    assert len(data["modularity_evidence"]) >= 3
    reference = data["methodology_references"][0]
    assert reference["key"] == "tang_2023_forecasting_pattern_recognition"
    assert reference["doi"] == "10.1016/j.ejrh.2023.101406"
    assert "Tang, Y." in reference["citation"]
    assert "Xin'anjiang" in reference["relevance"]


def test_regions_global_list():
    response = client.get("/regions")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 27
    assert {"country", "lat", "lon", "risk_baseline"}.issubset(rows[0].keys())


def test_model_status_reports_fallback_when_credentials_missing(monkeypatch):
    from app.api.routes import model_status as model_status_route

    monkeypatch.setattr(model_status_route, "credentials_available", lambda: False)
    response = client.get("/model-status")

    assert response.status_code == 200
    data = response.json()
    assert data["backend_status"] == "ok"
    assert data["data_mode"] == "fallback_open_meteo_proxy"
    assert data["fallback_active"] is True
    assert data["copernicus_credentials_configured"] is False
    assert data["publishable_predictions"] is False
    assert data["validation_status"] == "fallback_not_ground_truth_validated"


def test_model_status_reports_sentinel_mode_when_credentials_exist(monkeypatch):
    from app.api.routes import model_status as model_status_route

    monkeypatch.setattr(model_status_route, "credentials_available", lambda: True)
    response = client.get("/model-status")

    assert response.status_code == 200
    data = response.json()
    assert data["data_mode"] == "copernicus_sentinel"
    assert data["fallback_active"] is False
    assert data["copernicus_credentials_configured"] is True
    assert data["publishable_predictions"] is True
    assert data["validation_status"] == "sentinel_scene_ready_for_unosat_audit"


def test_forecast_full_success(monkeypatch):
    from app.services import forecaster

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, params):
            if url == forecaster.FORECAST_URL:
                return FakeResponse(
                    {
                        "daily": {"time": ["2026-06-12", "2026-06-13"], "precipitation_sum": [20.0, 4.0]},
                        "hourly": {
                            "time": ["2026-06-12T00:00", "2026-06-12T01:00", "2026-06-13T00:00"],
                            "soil_moisture_0_to_1cm": [0.2, 0.3, 0.1],
                        },
                    }
                )
            return FakeResponse({"daily": {"time": ["2026-06-12", "2026-06-13"], "river_discharge_mean": [100.0, 110.0]}})

    monkeypatch.setattr(forecaster.httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    response = client.post("/forecast", json={"country": "Bangladesh", "lat": 23.685, "lon": 90.3563})

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 5
    assert rows[0]["forecast_status"] == "ok"
    assert rows[0]["river_discharge_status"] == "available"
    assert rows[0]["river_discharge"] == 100.0
    assert rows[0]["soil_moisture"] == 0.25
    assert rows[0]["data_source"] == "open_meteo_weather"


def test_forecast_weather_only_when_river_fails(monkeypatch):
    from app.services import forecaster

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"daily": {"time": ["2026-06-12"], "precipitation_sum": [12.0]}, "hourly": {}}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, params):
            if url == forecaster.FLOOD_URL:
                raise RuntimeError("river unavailable")
            return FakeResponse()

    monkeypatch.setattr(forecaster.httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    response = client.post("/forecast", json={"country": "Bangladesh", "lat": 23.685, "lon": 90.3563})

    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["forecast_status"] == "weather_only"
    assert rows[0]["warning"] is True
    assert rows[0]["river_discharge_status"] == "unavailable"
    assert rows[0]["soil_moisture"] is None
    assert "weather inputs only" in rows[0]["status_note"]


def test_forecast_total_fallback_when_weather_fails(monkeypatch):
    from app.services import forecaster

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url, params):
            raise RuntimeError("network unavailable")

    monkeypatch.setattr(forecaster.httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    response = client.post("/forecast", json={"country": "Bangladesh", "lat": 23.685, "lon": 90.3563})

    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["forecast_status"] == "fallback"
    assert rows[0]["data_source"] == "fallback"
    assert rows[0]["status_note"] == "Open-Meteo weather forecast failed; using conservative fallback rows."
    assert rows[0]["flood_likelihood"] == 0.1


def test_scene_prediction_aggregation_resists_single_patch_spikes():
    dry_scene = summarize_scene_prediction([0.01] * 16)
    mixed_scene = summarize_scene_prediction([0.01] * 11 + [0.99] * 5)

    assert dry_scene["risk_level"] == "Low"
    assert dry_scene["classification"] == "no_flood"
    assert mixed_scene["risk_level"] == "Medium"
    assert mixed_scene["classification"] == "no_flood"
    assert mixed_scene["flood_probability"] < 0.5


def test_patch_hotspots_stay_inside_scene_bbox():
    hotspots = patch_hotspots([0.1, 0.8, 0.2, 0.7], 23.685, 90.3563, 50.0, limit=2)

    assert len(hotspots) == 2
    assert hotspots[0]["probability"] == 0.8
    assert all(23.2 < item["lat"] < 24.2 for item in hotspots)
    assert all(89.8 < item["lon"] < 90.9 for item in hotspots)


def test_predict_fallback_response_is_not_publishable(monkeypatch):
    from app.api.routes import predict as predict_route

    async def fake_scene(*_args, **_kwargs):
        return {
            "source": "fallback",
            "date": "2024-09-04",
            "rain_7d_mm": 12.0,
            "max_daily_rain_mm": 6.0,
            "water_signal": 0.25,
        }

    monkeypatch.setattr(predict_route, "fetch_satellite_scene", fake_scene)
    monkeypatch.setattr(predict_route, "scene_patch_probabilities", lambda _scene: [0.2, 0.3, 0.4, 0.1])
    response = client.post("/predict", json={"country": "Bangladesh", "lat": 23.685, "lon": 90.3563, "date": "2024-09-04"})

    assert response.status_code == 200
    data = response.json()
    assert data["data_source"] == "fallback"
    assert data["operational_mode"] == "fallback_open_meteo_proxy"
    assert data["publishable"] is False
    assert data["validation_status"] == "fallback_not_ground_truth_validated"
    assert data["confidence"] <= 0.65


def test_batch_regions_contract(monkeypatch):
    from app.api.routes import predict as predict_route

    async def fake_compute(payload):
        risk = "High" if payload.country == "Bangladesh" else "Low"
        return {
            "flood_probability": 0.8 if risk == "High" else 0.1,
            "risk_level": risk,
            "classification": "flood" if risk == "High" else "no_flood",
            "confidence": 0.65,
            "data_source": "fallback",
            "date": payload.date,
            "validation_status": "fallback_not_ground_truth_validated",
            "validation_note": "test",
            "rain_7d_mm": 10.0,
            "max_daily_rain_mm": 4.0,
            "water_signal": 0.2,
            "hotspots": [],
        }

    monkeypatch.setattr(predict_route, "compute_prediction", fake_compute)
    response = client.post("/predict/batch/regions", json={"date": "2024-09-04"})

    assert response.status_code == 200
    data = response.json()
    assert data["scope"] == "seeded_monitoring_regions"
    assert data["compute_mode"] == "classical_async_bounded_concurrency"
    assert data["total"] >= 27
    assert data["completed"] == data["total"]
    assert data["failed"] == 0
    assert data["high"] >= 1
    assert {"country", "lat", "lon", "status", "prediction"}.issubset(data["results"][0].keys())


def test_bangladesh_2024_validation_scenario(monkeypatch):
    from app.api.routes import validation as validation_route

    monkeypatch.setattr(validation_route, "_unosat_labels", lambda: [PatchLabel("UNOSAT-2024-00-00", 90.1, 23.6, 1)])
    response = client.get("/validation/scenarios/bangladesh-2024")

    assert response.status_code == 200
    data = response.json()
    assert data["source"]["event_code"] == "FL20240825BGD"
    assert data["ground_truth_hotspots"][0]["lat"] == 23.6
    assert data["ground_truth_hotspots"][0]["flood_class"] == "Satellite-detected flood extent"
    assert data["ground_truth_hotspots"][0]["details"]["patch_id"] == "UNOSAT-2024-00-00"
    assert data["ground_truth_hotspots"][0]["data"]["source_product_id"] == "3954"
    assert data["model_hotspots"] == []
    assert data["prediction"]["data_source"] == "local_unosat_ground_truth"
    assert data["prediction"]["operational_mode"] == "local_ground_truth_coordinate_scenario"
    assert data["prediction"]["publishable"] is True


def test_surface_water_prior_has_arid_controls():
    assert _surface_water_prior(23.685, 90.3563) > _surface_water_prior(23.0, 12.0)
    assert _surface_water_prior(-23.0, -70.0) == 0.0


def test_feature_extraction_length_and_label():
    patch = np.zeros((4, 64, 64), dtype=float)
    patch[3, :10, :10] = 0.4
    assert len(extract_patch_features(patch)) == 61
    assert label_patch(patch) == 0
    patch[3, :20, :20] = 0.4
    assert label_patch(patch) == 1


def test_preprocess_scene_records():
    size = 128
    scene = {
        "B03": np.full((size, size), 0.55),
        "B04": np.full((size, size), 0.25),
        "B08": np.full((size, size), 0.20),
        "VV": np.full((size, size), -15.0),
        "QA60": np.zeros((size, size), dtype=np.uint16),
        "date": "2024-08-01",
    }
    records = preprocess_scene(scene)
    assert len(records) == 4
    assert len(records[0]["features"]) == 61
    assert all(np.isfinite(records[0]["features"]))
    assert records[0]["label"] == 1


def test_indices():
    b3 = np.array([[0.6]])
    b4 = np.array([[0.2]])
    b8 = np.array([[0.3]])
    ndwi, ndvi = compute_indices(b3, b4, b8)
    assert round(float(ndwi[0, 0]), 3) == 0.333
    assert round(float(ndvi[0, 0]), 3) == 0.2


def test_synthetic_training_data_shape_and_ratios(tmp_path, monkeypatch):
    X, y = generate_synthetic_training_data()
    assert X.shape == (6768, 61)
    assert y.shape == (6768,)
    assert 0.20 < float(np.mean(y)) < 0.23


def test_train_predict_small_model(tmp_path, monkeypatch):
    from app.services import classifier as classifier_module

    monkeypatch.setattr(classifier_module, "MODEL_PATH", tmp_path / "xgboost_model.pkl")
    X, y = generate_synthetic_training_data()
    model = train(X[:600], y[:600])
    assert classifier_module.MODEL_PATH.exists()
    proba = model.predict_proba(X[:1])[0][1]
    assert 0.0 <= float(proba) <= 1.0


def test_independent_validation_summary_with_scores():
    labels = [
        PatchLabel("UNOSAT-2024-00-00", 90.0, 23.0, 0),
        PatchLabel("UNOSAT-2024-00-01", 90.1, 23.0, 1),
        PatchLabel("UNOSAT-2024-00-02", 90.2, 23.0, 1),
        PatchLabel("UNOSAT-2024-00-03", 90.3, 23.0, 0),
    ]
    scores = {
        "UNOSAT-2024-00-00": {"ndwi_water_fraction": 0.01, "model_probability": 0.2},
        "UNOSAT-2024-00-01": {"ndwi_water_fraction": 0.20, "model_probability": 0.9},
        "UNOSAT-2024-00-02": {"ndwi_water_fraction": 0.12, "model_probability": 0.8},
        "UNOSAT-2024-00-03": {"ndwi_water_fraction": 0.02, "model_probability": 0.1},
    }
    summary = summarize_validation(labels, scores)
    assert summary["metric_status"] == "computed"
    assert summary["ndwi_threshold_metrics"]["roc_auc"] == 1.0
    assert summary["model_probability_metrics"]["confusion_matrix"] == {"tn": 2, "fp": 0, "fn": 0, "tp": 2}
