from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import io
import json
import urllib.request
import zipfile

import numpy as np


UNOSAT_BANGLADESH_2024 = {
    "name": "UNOSAT FL20240825BGD",
    "product_id": "3954",
    "title": "Satellite detected water extents between 28 August & 4 September 2024 in Bangladesh",
    "source_url": "https://unosat.org/products/3954",
    "shapefile_url": "https://unosat.org/static/unosat_filesystem/3954/FL20240825BGD_SHP.zip",
    "event_code": "FL20240825BGD",
    "license": "Creative Commons Attribution Share-Alike (CC BY-SA)",
    "sensor": "Sentinel-1",
    "acquisition_window": "2024-08-18 to 2024-09-04",
    "published": "2024-09-08",
    "reported_flooded_area_km2": 8100,
    "reported_receded_area_km2": 8700,
    "reported_exposed_population": 6200000,
    "bbox": [88.00862798600008, 20.590609348000044, 92.68030687500004, 26.634513010000035],
    "caveat": "Preliminary satellite analysis; not field validated. Radar flood analysis can underestimate water in built-up or densely vegetated areas.",
}


@dataclass(frozen=True)
class PatchLabel:
    patch_id: str
    lon: float
    lat: float
    label: int


def download_unosat_shapefile(destination: Path) -> Path:
    """Download the UNOSAT shapefile ZIP if it is not already cached."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with urllib.request.urlopen(UNOSAT_BANGLADESH_2024["shapefile_url"], timeout=120) as response:
            destination.write_bytes(response.read())
    return destination


def _point_in_ring(lon: float, lat: float, ring: list[tuple[float, float]]) -> bool:
    inside = False
    if len(ring) < 3:
        return False
    x1, y1 = ring[-1]
    for x2, y2 in ring:
        intersects = (y1 > lat) != (y2 > lat)
        if intersects:
            x_intersection = (x2 - x1) * (lat - y1) / ((y2 - y1) or 1e-12) + x1
            if lon < x_intersection:
                inside = not inside
        x1, y1 = x2, y2
    return inside


def _shape_contains(shape: object, lon: float, lat: float) -> bool:
    bbox = getattr(shape, "bbox", None)
    if bbox and not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
        return False

    points = [(float(x), float(y)) for x, y in getattr(shape, "points")]
    parts = list(getattr(shape, "parts")) + [len(points)]
    contained = False
    for start, end in zip(parts[:-1], parts[1:], strict=True):
        if _point_in_ring(lon, lat, points[start:end]):
            contained = not contained
    return contained


def _index_rings(shapes: list[object]) -> list[tuple[tuple[float, float, float, float], list[tuple[float, float]]]]:
    indexed: list[tuple[tuple[float, float, float, float], list[tuple[float, float]]]] = []
    for shape in shapes:
        points = [(float(x), float(y)) for x, y in getattr(shape, "points")]
        parts = list(getattr(shape, "parts")) + [len(points)]
        for start, end in zip(parts[:-1], parts[1:], strict=True):
            ring = points[start:end]
            if len(ring) < 3:
                continue
            xs = [point[0] for point in ring]
            ys = [point[1] for point in ring]
            indexed.append(((min(xs), min(ys), max(xs), max(ys)), ring))
    return indexed


def _rings_contain(indexed_rings: list[tuple[tuple[float, float, float, float], list[tuple[float, float]]]], lon: float, lat: float) -> bool:
    contained = False
    for bbox, ring in indexed_rings:
        if bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3] and _point_in_ring(lon, lat, ring):
            contained = not contained
    return contained


def load_unosat_shapes(zip_path: Path) -> list[object]:
    """Read polygon shapes from the UNOSAT ZIP with the optional pyshp dependency."""

    try:
        import shapefile  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised by CLI users without pyshp.
        raise RuntimeError("Install pyshp to read UNOSAT shapefiles: pip install pyshp") from exc

    with zipfile.ZipFile(zip_path) as archive:
        members = {Path(name).suffix.lower(): name for name in archive.namelist() if Path(name).suffix.lower() in {".shp", ".shx", ".dbf"}}
        missing = {".shp", ".shx", ".dbf"} - members.keys()
        if missing:
            raise FileNotFoundError(f"UNOSAT ZIP is missing shapefile member(s): {', '.join(sorted(missing))}")
        reader = shapefile.Reader(
            shp=io.BytesIO(archive.read(members[".shp"])),
            shx=io.BytesIO(archive.read(members[".shx"])),
            dbf=io.BytesIO(archive.read(members[".dbf"])),
        )
        return list(reader.shapes())


def build_patch_labels(shapes: list[object], rows: int = 32, cols: int = 32) -> list[PatchLabel]:
    """Convert flood polygons to regular patch labels across the UNOSAT analysed extent."""

    min_lon, min_lat, max_lon, max_lat = UNOSAT_BANGLADESH_2024["bbox"]
    indexed_rings = _index_rings(shapes)
    lon_step = (max_lon - min_lon) / cols
    lat_step = (max_lat - min_lat) / rows
    candidates: list[list[list[tuple[tuple[float, float, float, float], list[tuple[float, float]]]]]] = [[[] for _col in range(cols)] for _row in range(rows)]
    for bbox, ring in indexed_rings:
        col_start = max(0, int(np.floor((bbox[0] - min_lon) / lon_step)))
        col_end = min(cols - 1, int(np.floor((bbox[2] - min_lon) / lon_step)))
        row_start = max(0, int(np.floor((max_lat - bbox[3]) / lat_step)))
        row_end = min(rows - 1, int(np.floor((max_lat - bbox[1]) / lat_step)))
        for row in range(row_start, row_end + 1):
            for col in range(col_start, col_end + 1):
                candidates[row][col].append((bbox, ring))
    labels: list[PatchLabel] = []
    for row in range(rows):
        lat = max_lat - (row + 0.5) * lat_step
        for col in range(cols):
            lon = min_lon + (col + 0.5) * lon_step
            is_flooded = _rings_contain(candidates[row][col], lon, lat)
            labels.append(PatchLabel(f"UNOSAT-2024-{row:02d}-{col:02d}", lon, lat, int(is_flooded)))
    return labels


def read_score_csv(path: Path) -> dict[str, dict[str, float]]:
    """Read patch-level model and NDWI scores keyed by patch_id."""

    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        required = {"patch_id", "ndwi_water_fraction", "model_probability"}
        if not required.issubset(rows.fieldnames or set()):
            raise ValueError(f"Score CSV must contain columns: {', '.join(sorted(required))}")
        return {
            row["patch_id"]: {
                "ndwi_water_fraction": float(row["ndwi_water_fraction"]),
                "model_probability": float(row["model_probability"]),
            }
            for row in rows
        }


def _metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float | int | dict[str, int]]:
    y_pred = (scores >= threshold).astype(int)
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    accuracy = (tp + tn) / max(1, y_true.size)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "patches": int(y_true.size),
        "roc_auc": round(_roc_auc(y_true, scores), 4),
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
    }


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


def classify_patch_error(label: int, probability: float | None, threshold: float = 0.5) -> str:
    """Return validation class using only UNOSAT as label and model score as prediction."""

    if probability is None:
        return "score_missing"
    predicted = int(probability >= threshold)
    if label == 1 and predicted == 1:
        return "true_positive"
    if label == 0 and predicted == 1:
        return "false_positive"
    if label == 1 and predicted == 0:
        return "false_negative"
    return "true_negative"


def build_patch_audit_rows(labels: list[PatchLabel], scores: dict[str, dict[str, float]] | None = None, threshold: float = 0.5) -> list[dict]:
    """Build per-patch audit rows for independent validation artifacts."""

    rows = []
    min_lon, min_lat, max_lon, max_lat = UNOSAT_BANGLADESH_2024["bbox"]
    for label in labels:
        score = scores.get(label.patch_id) if scores else None
        model_probability = score.get("model_probability") if score else None
        ndwi_water_fraction = score.get("ndwi_water_fraction") if score else None
        error_type = classify_patch_error(label.label, model_probability, threshold=threshold)
        rows.append(
            {
                "patch_id": label.patch_id,
                "lat": round(label.lat, 6),
                "lon": round(label.lon, 6),
                "scene_date": "2024-09-04",
                "scene_bounds": f"{min_lon},{min_lat},{max_lon},{max_lat}",
                "unosat_label": label.label,
                "ndwi_water_fraction": ndwi_water_fraction,
                "model_probability": model_probability,
                "prediction_class": "not_validation_ready" if model_probability is None else int(model_probability >= threshold),
                "error_type": error_type,
                "label_source": UNOSAT_BANGLADESH_2024["event_code"],
                "score_source": "provided_patch_score_csv" if score else "score_missing",
            }
        )
    return rows


def summarize_patch_audit(rows: list[dict]) -> dict:
    """Summarize patch-level validation artifact readiness and error classes."""

    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["error_type"])
        counts[key] = counts.get(key, 0) + 1
    scored_rows = [row for row in rows if row["model_probability"] is not None]
    flooded = [row for row in rows if int(row["unosat_label"]) == 1]
    return {
        "artifact_status": "computed" if scored_rows else "scores_required",
        "patches": len(rows),
        "scored_patches": len(scored_rows),
        "flooded_patches": len(flooded),
        "error_type_counts": counts,
        "evidence_tiers": [
            "ground_truth: UNOSAT flood labels only",
            "model_signal: Sentinel-derived NDWI/features and XGBoost probabilities when supplied",
            "operational_forecast: Open-Meteo context only, not validation",
        ],
        "publishable": bool(scored_rows) and not counts.get("score_missing"),
        "note": "Patch labels come from UNOSAT. NDWI water fraction and model probability are audited as independent score columns, never as label sources.",
    }


def summarize_validation(labels: list[PatchLabel], scores: dict[str, dict[str, float]] | None = None) -> dict:
    """Build an audit summary, adding metrics when real patch scores are supplied."""

    y_true = np.asarray([label.label for label in labels], dtype=int)
    summary = {
        "source": UNOSAT_BANGLADESH_2024,
        "ground_truth": {
            "patches": len(labels),
            "flooded_patches": int(y_true.sum()),
            "flooded_percent": round(float(y_true.mean() * 100), 2) if y_true.size else 0.0,
            "grid": "32x32 patch-centroid labels over the UNOSAT analysed extent",
        },
        "metric_status": "scores_required",
        "publishable": False,
        "metric_note": "Provide real patch-level NDWI water fractions and model probabilities with --scores-csv to compute publishable independent metrics.",
    }
    if scores is None:
        return summary

    matched = [label for label in labels if label.patch_id in scores]
    if not matched:
        raise ValueError("No score CSV patch_id values matched the generated UNOSAT labels")

    y_matched = np.asarray([label.label for label in matched], dtype=int)
    ndwi_scores = np.asarray([scores[label.patch_id]["ndwi_water_fraction"] for label in matched], dtype=float)
    model_scores = np.asarray([scores[label.patch_id]["model_probability"] for label in matched], dtype=float)
    summary.update(
        {
            "metric_status": "computed",
            "publishable": len(matched) == len(labels),
            "metric_note": "Metrics compare supplied patch scores against UNOSAT flood-extent labels; NDWI scores are not used as labels.",
            "ndwi_threshold_metrics": _metrics(y_matched, ndwi_scores, threshold=0.05),
            "model_probability_metrics": _metrics(y_matched, model_scores, threshold=0.5),
        }
    )
    return summary


def write_patch_audit(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "patch_id",
        "lat",
        "lon",
        "scene_date",
        "scene_bounds",
        "unosat_label",
        "ndwi_water_fraction",
        "model_probability",
        "prediction_class",
        "error_type",
        "label_source",
        "score_source",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
