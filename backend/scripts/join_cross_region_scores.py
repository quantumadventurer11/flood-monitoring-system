from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.cross_region_validation import VALIDATION_EVENTS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Spatially join cross-region labels and Sentinel predictions into final metric score CSVs.")
    parser.add_argument("--labels-dir", type=Path, default=ROOT / "validation" / "cross_region" / "labels")
    parser.add_argument("--predictions-dir", type=Path, default=ROOT / "validation" / "cross_region" / "predictions")
    parser.add_argument("--scores-dir", type=Path, default=ROOT / "validation" / "cross_region" / "scores")
    parser.add_argument("--status-output", type=Path, default=ROOT / "validation" / "cross_region" / "join_status.json")
    args = parser.parse_args()

    args.scores_dir.mkdir(parents=True, exist_ok=True)
    statuses = [_join_event(event, args.labels_dir, args.predictions_dir, args.scores_dir) for event in VALIDATION_EVENTS]
    args.status_output.write_text(json.dumps({"events": statuses}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.status_output}")
    for status in statuses:
        print(f"{status['key']}: {status['status']}")


def _join_event(event, labels_dir: Path, predictions_dir: Path, scores_dir: Path) -> dict:
    label_path = labels_dir / event.label_filename
    prediction_path = predictions_dir / event.prediction_filename
    score_path = scores_dir / event.score_filename
    if not label_path.exists():
        return _blocked(event, score_path, f"Missing label file: {label_path}")
    if not prediction_path.exists():
        return _blocked(event, score_path, f"Missing Sentinel prediction file: {prediction_path}")

    labels = _read_csv(label_path)
    predictions = _read_csv(prediction_path)
    if not labels:
        return _blocked(event, score_path, "Label file contains no rows")
    if not predictions:
        return _blocked(event, score_path, "Prediction file contains no rows")
    if any(row.get("data_source") != "copernicus" for row in predictions):
        return _blocked(event, score_path, "Prediction file contains non-Copernicus rows; refusing publication score CSV")

    output_rows = []
    for label in labels:
        nearest = min(predictions, key=lambda prediction: _distance(float(label["lat"]), float(label["lon"]), float(prediction["lat"]), float(prediction["lon"])))
        output_rows.append(
            {
                "patch_id": label["patch_id"],
                "ground_truth_label": int(float(label["ground_truth_label"])),
                "model_probability": float(nearest["model_probability"]),
                "ndwi_water_fraction": float(nearest.get("ndwi_water_fraction") or 0.0),
                "lat": float(label["lat"]),
                "lon": float(label["lon"]),
                "runtime_seconds": float(nearest.get("runtime_seconds") or 0.0),
                "label_source": label.get("label_source", ""),
                "prediction_patch_id": nearest.get("patch_id", ""),
            }
        )

    label_values = {row["ground_truth_label"] for row in output_rows}
    if label_values != {0, 1}:
        return _blocked(event, score_path, "Joined rows do not contain both flooded and non-flooded labels")

    with score_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["patch_id", "ground_truth_label", "model_probability", "ndwi_water_fraction", "lat", "lon", "runtime_seconds", "label_source", "prediction_patch_id"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    flooded = sum(row["ground_truth_label"] for row in output_rows)
    return {
        "key": event.key,
        "location": event.location,
        "status": "ready",
        "score_file": str(score_path.relative_to(ROOT)),
        "patches": len(output_rows),
        "flooded_patches": flooded,
        "non_flooded_patches": len(output_rows) - flooded,
        "blocker": None,
    }


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _blocked(event, score_path: Path, blocker: str) -> dict:
    return {
        "key": event.key,
        "location": event.location,
        "status": "blocked",
        "score_file": str(score_path.relative_to(ROOT)),
        "blocker": blocker,
    }


def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return math.hypot(lat1 - lat2, lon1 - lon2)


if __name__ == "__main__":
    main()
