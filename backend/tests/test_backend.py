import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.services.preprocessing import compute_indices, extract_patch_features, label_patch


client = TestClient(app)


def test_paper_results_exact_values():
    data = client.get("/paper-results").json()
    assert data["dataset_stats"][0]["total_patches"] == 2630
    assert data["model_metrics"][0]["model"] == "XGBoost"
    assert data["model_metrics"][0]["f1"] == 0.923


def test_prediction_shape():
    response = client.post("/predict", json={"country": "Bangladesh", "lat": 23.8103, "lon": 90.4125, "date": "2024-08-01"})
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"flood_probability", "risk_level", "classification", "confidence"}


def test_feature_extraction_length_and_label():
    patch = np.zeros((4, 64, 64), dtype=float)
    patch[3, :10, :10] = 0.4
    assert len(extract_patch_features(patch)) == 61
    assert label_patch(patch) == 0
    patch[3, :20, :20] = 0.4
    assert label_patch(patch) == 1


def test_indices():
    b3 = np.array([[0.6]])
    b4 = np.array([[0.2]])
    b8 = np.array([[0.3]])
    ndwi, ndvi = compute_indices(b3, b4, b8)
    assert round(float(ndwi[0, 0]), 3) == 0.333
    assert round(float(ndvi[0, 0]), 3) == 0.2
