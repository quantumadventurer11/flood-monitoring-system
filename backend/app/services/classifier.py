from pathlib import Path

import joblib
import numpy as np
from sklearn.model_selection import train_test_split
import xgboost as xgb

from app.services.risk import classification, risk_level


MODEL_PATH = Path(__file__).resolve().parents[1] / "ml" / "xgboost_model_ndwi_free.pkl"
FEATURE_COUNT = 61
NDWI_FEATURE_INDICES = set(range(45, 60)) | {60}
MODEL_FEATURE_INDICES = [index for index in range(FEATURE_COUNT) if index not in NDWI_FEATURE_INDICES]
PAPER_MONTHS = [
    ("June", 2630, 0.418),
    ("July", 2249, 0.133),
    ("August", 1889, 0.039),
]


def _make_feature_vector(rng: np.random.Generator, flooded: bool) -> np.ndarray:
    """Generate one realistic 61-feature vector matching the paper feature layout."""

    features: list[float] = []
    band_profiles = [
        (-0.20, 0.23),  # VV
        (0.05, 0.18),  # B04
        (0.14 if not flooded else -0.05, 0.20),  # NDVI
        (0.18 if flooded else -0.24, 0.16),  # NDWI
    ]
    for band_index, (mean, std) in enumerate(band_profiles):
        jittered_mean = rng.normal(mean, std * 0.18)
        band_std = abs(rng.normal(std, std * 0.15))
        min_value = np.clip(jittered_mean - rng.uniform(1.5, 2.5) * band_std, -1, 1)
        max_value = np.clip(jittered_mean + rng.uniform(1.5, 2.5) * band_std, -1, 1)
        median = np.clip(jittered_mean + rng.normal(0, band_std * 0.08), -1, 1)
        skewness = rng.normal(0.55 if flooded and band_index == 3 else 0.0, 0.35)
        kurt = rng.normal(0.4, 0.4)
        p5, p25, p75, p95 = np.clip(
            [
                jittered_mean - 1.65 * band_std,
                jittered_mean - 0.67 * band_std,
                jittered_mean + 0.67 * band_std,
                jittered_mean + 1.65 * band_std,
            ],
            -1,
            1,
        )
        contrast = abs(rng.normal(18 if band_index in {0, 3} else 10, 4))
        homogeneity = float(np.clip(rng.normal(0.62, 0.08), 0, 1))
        energy = float(np.clip(rng.normal(0.18, 0.05), 0, 1))
        correlation = float(np.clip(rng.normal(0.55, 0.16), -1, 1))
        features.extend(
            [
                jittered_mean,
                band_std,
                min_value,
                max_value,
                median,
                skewness,
                kurt,
                p5,
                p25,
                p75,
                p95,
                contrast,
                homogeneity,
                energy,
                correlation,
            ]
        )

    water_fraction = float(np.clip(rng.normal(0.24, 0.11), 0.06, 0.85)) if flooded else float(np.clip(rng.normal(0.018, 0.014), 0, 0.049))
    features.append(water_fraction)
    return np.array(features, dtype=float)


def generate_synthetic_training_data(seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Generate 6,768 paper-shaped synthetic examples for first-run training."""

    rng = np.random.default_rng(seed)
    rows: list[np.ndarray] = []
    labels: list[int] = []
    for _month, count, flood_ratio in PAPER_MONTHS:
        flood_count = int(round(count * flood_ratio))
        month_labels = np.array([1] * flood_count + [0] * (count - flood_count))
        rng.shuffle(month_labels)
        for label in month_labels:
            rows.append(_make_feature_vector(rng, bool(label)))
            labels.append(int(label))
    return np.vstack(rows), np.array(labels, dtype=int)


def train(X: np.ndarray, y: np.ndarray) -> xgb.XGBClassifier:
    """Train and persist an XGBoost binary flood classifier without NDWI-derived inputs."""

    positives = int(np.sum(y == 1))
    negatives = int(np.sum(y == 0))
    scale_pos_weight = negatives / max(1, positives)
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42,
    )
    X_model = X[:, MODEL_FEATURE_INDICES]
    X_train, _X_val, y_train, _y_val = train_test_split(X_model, y, test_size=0.2, stratify=y, random_state=42)
    model.fit(X_train, y_train)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return model


class FloodClassifier:
    """XGBoost model loader and predictor."""

    def __init__(self) -> None:
        self.model: xgb.XGBClassifier | None = None

    def load(self) -> xgb.XGBClassifier:
        if self.model is None:
            if not MODEL_PATH.exists():
                X, y = generate_synthetic_training_data()
                self.model = train(X, y)
            else:
                self.model = joblib.load(MODEL_PATH)
        return self.model

    def predict(self, features: list[float]) -> dict[str, float | str]:
        if len(features) != FEATURE_COUNT:
            raise ValueError(f"Expected {FEATURE_COUNT} features, received {len(features)}")
        model = self.load()
        model_features = np.asarray([[features[index] for index in MODEL_FEATURE_INDICES]], dtype=float)
        proba = float(model.predict_proba(model_features)[0][1])
        proba = float(np.clip(proba, 0.0, 1.0))
        return {
            "flood_probability": round(proba, 4),
            "classification": classification(proba),
            "risk_level": risk_level(proba),
            "confidence": round(max(proba, 1 - proba), 4),
        }


classifier = FloodClassifier()


def ensure_model() -> xgb.XGBClassifier:
    """Load or train the persisted XGBoost model."""

    return classifier.load()


def predict(features: list[float]) -> dict[str, float | str]:
    """Predict flood risk from one 61-feature vector."""

    return classifier.predict(features)
