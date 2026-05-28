from datetime import date

import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.services.classifier import generate_synthetic_training_data, train
from app.services.preprocessing import compute_indices, extract_patch_features, label_patch, preprocess_scene
from seed_db import seed


seed()
client = TestClient(app)


def test_paper_results_exact_values():
    data = client.get("/paper-results").json()
    assert data["dataset_stats"][0]["total_patches"] == 2630
    assert data["model_metrics"][0]["model"] == "XGBoost"
    assert data["model_metrics"][0]["f1"] == 0.923


def test_regions_global_list():
    response = client.get("/regions")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 27
    assert {"country", "lat", "lon", "risk_baseline"}.issubset(rows[0].keys())


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
