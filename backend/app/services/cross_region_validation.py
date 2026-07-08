from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import time

import numpy as np

from app.services.classifier import MODEL_PATH, ensure_model
from app.services.satellite import credentials_available


ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ROOT.parent
REFERENCES_PATH = PROJECT_ROOT / "references"


@dataclass(frozen=True)
class ValidationEvent:
    key: str
    location: str
    event_name: str
    event_period: str
    validation_date: str
    lat: float
    lon: float
    buffer_km: float
    bbox: str
    ground_truth_source: str
    ground_truth_url: str
    reference_urls: tuple[str, ...]
    label_filename: str
    prediction_filename: str
    score_filename: str


VALIDATION_EVENTS: tuple[ValidationEvent, ...] = (
    ValidationEvent(
        key="bangladesh_2024",
        location="Bangladesh",
        event_name="August/September 2024 Bangladesh floods",
        event_period="2024-08-28 to 2024-09-04",
        validation_date="2024-09-04",
        lat=24.462485,
        lon=90.417462,
        buffer_km=50.0,
        bbox="50 km validation buffer around UNOSAT flood cluster near 24.462485,90.417462; UNOSAT source extent is broader",
        ground_truth_source="UNOSAT FL20240825BGD product 3954",
        ground_truth_url="https://unosat.org/products/3954",
        reference_urls=(
            "https://unosat.org/products/3954",
            "https://unosat.org/static/unosat_filesystem/3954/FL20240825BGD_SHP.zip",
        ),
        label_filename="bangladesh_2024_ground_truth_labels.csv",
        prediction_filename="bangladesh_2024_sentinel_predictions.csv",
        score_filename="bangladesh_2024_patch_scores.csv",
    ),
    ValidationEvent(
        key="pakistan_2022",
        location="Pakistan",
        event_name="August 2022 monsoon floods",
        event_period="2022-08-03 to 2022-08-23",
        validation_date="2022-08-23",
        lat=26.734,
        lon=67.779,
        buffer_km=50.0,
        bbox="50 km validation buffer around Sindh flood area near 26.734,67.779; refine after geospatial source download",
        ground_truth_source="UNOSAT/Copernicus flood extent product to be converted to patch labels",
        ground_truth_url="Locate product titled 'Satellite detected water extents between 03 and 23 August 2022 over Pakistan'",
        reference_urls=(
            "https://www.bbc.com/news/world-asia-62728678",
            "https://www.axios.com/2022/09/07/pakistan-floods-death-toll-climate-change",
            "https://time.com/6209967/pakistan-floods-what-to-know/",
        ),
        label_filename="pakistan_2022_ground_truth_labels.csv",
        prediction_filename="pakistan_2022_sentinel_predictions.csv",
        score_filename="pakistan_2022_patch_scores.csv",
    ),
    ValidationEvent(
        key="mozambique_2023",
        location="Mozambique",
        event_name="Cyclone Freddy floods",
        event_period="2023-03-11 to 2023-03-15",
        validation_date="2023-03-13",
        lat=-17.878,
        lon=36.889,
        buffer_km=50.0,
        bbox="50 km validation buffer around Quelimane/Zambezia near -17.878,36.889; refine after geospatial source download",
        ground_truth_source="UNOSAT/Copernicus flood extent product to be converted to patch labels",
        ground_truth_url="Locate product titled 'Satellite detected water extent over Sofala and Zambezia Provinces, Mozambique as of 13 Mar. 2023'",
        reference_urls=(
            "https://apnews.com/article/80954c31303f3370aa175a8f4f9d917d",
            "https://apnews.com/article/7a0949c6ea48dec4fa772f5d05c494d5",
            "https://reliefweb.int/",
        ),
        label_filename="mozambique_2023_ground_truth_labels.csv",
        prediction_filename="mozambique_2023_sentinel_predictions.csv",
        score_filename="mozambique_2023_patch_scores.csv",
    ),
)


def read_patch_score_csv(path: Path) -> list[dict]:
    """Read real per-patch labels and model probabilities for one validation event."""

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"patch_id", "ground_truth_label", "model_probability"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing required column(s): {', '.join(sorted(missing))}")

        rows = []
        for row in reader:
            rows.append(
                {
                    "patch_id": row["patch_id"],
                    "ground_truth_label": int(float(row["ground_truth_label"])),
                    "model_probability": float(row["model_probability"]),
                    "runtime_seconds": _optional_float(row.get("runtime_seconds")),
                    "lat": _optional_float(row.get("lat")),
                    "lon": _optional_float(row.get("lon")),
                    "ndwi_water_fraction": _optional_float(row.get("ndwi_water_fraction")),
                }
            )
    if not rows:
        raise ValueError(f"{path} does not contain any patch rows")
    return rows


def binary_metrics(labels: list[int], scores: list[float], threshold: float = 0.5) -> dict:
    """Calculate AUC ROC, accuracy, precision, recall, and F1 from real labels/scores."""

    y_true = np.asarray(labels, dtype=int)
    y_score = np.asarray(scores, dtype=float)
    y_pred = (y_score >= threshold).astype(int)
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    accuracy = (tp + tn) / max(1, y_true.size)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "auc_roc": round(_roc_auc(y_true, y_score), 4),
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


def evaluate_event(event: ValidationEvent, scores_dir: Path) -> dict:
    """Evaluate one event if its real patch-score CSV exists; otherwise return a blocker."""

    score_path = scores_dir / event.score_filename
    cross_region_root = scores_dir.parent
    label_path = cross_region_root / "labels" / event.label_filename
    prediction_path = cross_region_root / "predictions" / event.prediction_filename
    base = {
        "key": event.key,
        "location": event.location,
        "event_name": event.event_name,
        "event_period": event.event_period,
        "validation_date": event.validation_date,
        "lat": event.lat,
        "lon": event.lon,
        "buffer_km": event.buffer_km,
        "bbox": event.bbox,
        "reference_saved": REFERENCES_PATH.exists(),
        "ground_truth_source": event.ground_truth_source,
        "ground_truth_url": event.ground_truth_url,
        "label_file": str(label_path.relative_to(PROJECT_ROOT)) if label_path.is_relative_to(PROJECT_ROOT) else str(label_path),
        "label_status": "ready" if label_path.exists() else "missing",
        "prediction_file": str(prediction_path.relative_to(PROJECT_ROOT)) if prediction_path.is_relative_to(PROJECT_ROOT) else str(prediction_path),
        "prediction_status": "ready" if prediction_path.exists() else "missing",
        "score_file": str(score_path.relative_to(PROJECT_ROOT)) if score_path.is_relative_to(PROJECT_ROOT) else str(score_path),
    }
    if not score_path.exists():
        return {
            **base,
            "metric_status": "scores_required",
            "publishable": False,
            "patches": None,
            "auc_roc": None,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "time_seconds": None,
            "blocker": "Missing real patch-score CSV with ground_truth_label and model_probability columns.",
        }

    started = time.perf_counter()
    rows = read_patch_score_csv(score_path)
    elapsed = time.perf_counter() - started
    labels = [int(row["ground_truth_label"]) for row in rows]
    scores = [float(row["model_probability"]) for row in rows]
    if len(set(labels)) < 2:
        raise ValueError(f"{score_path} must contain both flood and non-flood labels to compute AUC ROC")

    metrics = binary_metrics(labels, scores)
    supplied_runtime = [row["runtime_seconds"] for row in rows if row["runtime_seconds"] is not None]
    return {
        **base,
        "metric_status": "computed",
        "publishable": True,
        "patches": len(rows),
        **metrics,
        "time_seconds": round(float(sum(supplied_runtime) if supplied_runtime else elapsed), 4),
        "blocker": None,
    }


def build_cross_region_report(scores_dir: Path | None = None) -> dict:
    """Build the cross-region validation report and app health summary."""

    scores_root = scores_dir or ROOT / "validation" / "cross_region" / "scores"
    event_results = [evaluate_event(event, scores_root) for event in VALIDATION_EVENTS]
    computed = [row for row in event_results if row["metric_status"] == "computed"]
    overall = _overall_metrics(scores_root, computed)
    health = app_health_report()
    blockers = [row["blocker"] for row in event_results if row.get("blocker")]
    if not credentials_available():
        blockers.append("Copernicus credentials are not configured; fallback proxy predictions are not acceptable for final validation metrics.")
    return {
        "metric_status": "computed" if len(computed) == len(VALIDATION_EVENTS) else "scores_required",
        "publishable": len(computed) == len(VALIDATION_EVENTS) and health["status"] == "pass" and credentials_available(),
        "references_file": str(REFERENCES_PATH.relative_to(PROJECT_ROOT)),
        "scores_dir": str(scores_root.relative_to(PROJECT_ROOT)) if scores_root.is_relative_to(PROJECT_ROOT) else str(scores_root),
        "events": event_results,
        "overall": overall,
        "health": health,
        "blockers": blockers,
        "fix_plan": _fix_plan(blockers, health),
    }


def write_cross_region_outputs(report: dict, output_dir: Path) -> None:
    """Write JSON, CSV, and Markdown summaries for cross-region validation."""

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _write_events_csv(report["events"], report["overall"], output_dir / "summary.csv")
    _write_markdown_summary(report, output_dir / "summary.md")


def app_health_report() -> dict:
    """Check app endpoints and model load state without accepting fallback validation as publishable."""

    checks = []

    def record(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    record("references_file", REFERENCES_PATH.exists(), "references file exists" if REFERENCES_PATH.exists() else "references file is missing")
    try:
        ensure_model()
        record("model_load", MODEL_PATH.exists(), "model artifact is present after ensure_model")
    except Exception as exc:  # pragma: no cover - defensive health reporting.
        record("model_load", False, str(exc))

    try:
        from fastapi.testclient import TestClient

        from app.main import app

        with TestClient(app) as client:
            health = client.get("/health")
            record("health_endpoint", health.status_code == 200 and health.json().get("status") == "ok", f"status={health.status_code}")
            model_status = client.get("/model-status")
            record("model_status_endpoint", model_status.status_code == 200 and model_status.json().get("backend_status") == "ok", f"status={model_status.status_code}")
            regions = client.get("/regions")
            record("regions_endpoint", regions.status_code == 200 and len(regions.json()) >= 3, f"status={regions.status_code}, regions={len(regions.json()) if regions.status_code == 200 else 0}")
    except Exception as exc:  # pragma: no cover - defensive health reporting.
        record("api_startup", False, str(exc))

    return {
        "status": "pass" if all(check["ok"] for check in checks) else "fail",
        "checks": checks,
        "validation_note": "App health passing does not make fallback proxy predictions publishable; real Sentinel-backed scores and geospatial labels are still required.",
    }


def _overall_metrics(scores_dir: Path, computed_events: list[dict]) -> dict | None:
    if not computed_events:
        return None
    labels: list[int] = []
    scores: list[float] = []
    total_time = 0.0
    for event in VALIDATION_EVENTS:
        if not any(row["key"] == event.key for row in computed_events):
            continue
        rows = read_patch_score_csv(scores_dir / event.score_filename)
        labels.extend(int(row["ground_truth_label"]) for row in rows)
        scores.extend(float(row["model_probability"]) for row in rows)
        total_time += float(next(row["time_seconds"] for row in computed_events if row["key"] == event.key) or 0.0)
    return {"patches": len(labels), **binary_metrics(labels, scores), "time_seconds": round(total_time, 4)}


def _write_events_csv(events: list[dict], overall: dict | None, path: Path) -> None:
    fieldnames = ["location", "event_period", "reference_saved", "ground_truth_source", "label_status", "prediction_status", "patches", "auc_roc", "accuracy", "precision", "recall", "f1", "time_seconds", "metric_status", "blocker"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow({name: event.get(name) for name in fieldnames})
        if overall:
            writer.writerow(
                {
                    "location": "Overall",
                    "event_period": "Combined",
                    "reference_saved": True,
                    "ground_truth_source": "Combined official geospatial labels",
                    "label_status": "ready",
                    "prediction_status": "ready",
                    "patches": overall.get("patches"),
                    "auc_roc": overall.get("auc_roc"),
                    "accuracy": overall.get("accuracy"),
                    "precision": overall.get("precision"),
                    "recall": overall.get("recall"),
                    "f1": overall.get("f1"),
                    "time_seconds": overall.get("time_seconds"),
                    "metric_status": "computed",
                    "blocker": None,
                }
            )


def _write_markdown_summary(report: dict, path: Path) -> None:
    rows = [
        "| Location | Event Period | Reference Saved | Labels | Sentinel Predictions | Patches | AUC ROC | Accuracy | Precision | Recall | F1 | Time | Status |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for event in report["events"]:
        rows.append(
            "| {location} | {event_period} | {reference_saved} | {label_status} | {prediction_status} | {patches} | {auc_roc} | {accuracy} | {precision} | {recall} | {f1} | {time_seconds} | {metric_status} |".format(
                **{key: _display(value) for key, value in event.items()}
            )
        )
    overall = report.get("overall")
    if overall:
        rows.append(
            "| Overall | Combined | True | ready | ready | {patches} | {auc_roc} | {accuracy} | {precision} | {recall} | {f1} | {time_seconds} | computed |".format(
                **{key: _display(value) for key, value in overall.items()}
            )
        )
    blockers = "\n".join(f"- {blocker}" for blocker in report["blockers"]) or "- None"
    path.write_text(
        "# Cross-Region Validation Summary\n\n"
        + "\n".join(rows)
        + "\n\n## Health\n\n"
        + f"- App health status: `{report['health']['status']}`\n"
        + f"- Publishable: `{report['publishable']}`\n\n"
        + "## Blockers\n\n"
        + blockers
        + "\n",
        encoding="utf-8",
    )


def _fix_plan(blockers: list[str], health: dict) -> list[str]:
    fixes = []
    if any("patch-score CSV" in blocker for blocker in blockers):
        fixes.append("Generate final patch-score CSVs by spatially joining ground-truth label CSVs with Sentinel-backed prediction CSVs for each event.")
    if any("Copernicus credentials" in blocker for blocker in blockers):
        fixes.append("Configure Copernicus credentials so validation scores come from real Sentinel scenes instead of fallback proxy arrays.")
    if health["status"] != "pass":
        failed = [check["name"] for check in health["checks"] if not check["ok"]]
        fixes.append(f"Fix failing app health checks before accepting validation: {', '.join(failed)}.")
    return fixes


def _roc_auc(y_true: np.ndarray, scores: np.ndarray) -> float:
    positives = scores[y_true == 1]
    negatives = scores[y_true == 0]
    if positives.size == 0 or negatives.size == 0:
        return 0.0
    wins = 0.0
    for value in positives:
        wins += float(np.sum(value > negatives))
        wins += 0.5 * float(np.sum(value == negatives))
    return wins / float(positives.size * negatives.size)


def _optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def _display(value: object) -> object:
    return "TBD" if value is None else value
