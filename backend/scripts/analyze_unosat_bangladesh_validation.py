from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.independent_validation import (  # noqa: E402
    PatchLabel,
    UNOSAT_BANGLADESH_2024,
    _index_rings,
    _metrics,
    _rings_contain,
    download_unosat_shapefile,
    load_unosat_shapes,
    read_score_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze real UNOSAT Bangladesh validation failures and label-margin ablation.")
    parser.add_argument("--scores-csv", type=Path, default=ROOT / "validation" / "bangladesh_2024_real_scores.csv")
    parser.add_argument("--audit-csv", type=Path, default=ROOT / "validation" / "audits" / "bangladesh_2024" / "patch_level_audit.csv")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".validation_cache")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "validation" / "audits" / "bangladesh_2024")
    args = parser.parse_args()

    rows = _read_audit_rows(args.audit_csv)
    failure_summary = _failure_summary(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "failure_analysis.json").write_text(json.dumps(failure_summary, indent=2) + "\n", encoding="utf-8")

    shapes = load_unosat_shapes(download_unosat_shapefile(args.cache_dir / "FL20240825BGD_SHP.zip"))
    scores = read_score_csv(args.scores_csv)
    ablation_rows = _buffer_ablation(shapes, scores)
    _write_ablation_csv(ablation_rows, args.output_dir / "buffer_ablation.csv")
    _write_markdown(failure_summary, ablation_rows, args.output_dir / "failure_analysis.md")
    print(f"Wrote {args.output_dir / 'failure_analysis.json'}")
    print(f"Wrote {args.output_dir / 'buffer_ablation.csv'}")
    print(f"Wrote {args.output_dir / 'failure_analysis.md'}")


def _read_audit_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _failure_summary(rows: list[dict]) -> dict:
    by_type: dict[str, list[dict]] = {}
    for row in rows:
        by_type.setdefault(row["error_type"], []).append(row)

    return {
        "source": "Real Copernicus Sentinel scores compared with UNOSAT FL20240825BGD patch labels.",
        "important_caveat": UNOSAT_BANGLADESH_2024["caveat"],
        "counts": {key: len(value) for key, value in sorted(by_type.items())},
        "groups": {key: _describe_group(value) for key, value in sorted(by_type.items())},
        "interpretation": [
            "The model over-predicts flood at the default 0.5 threshold: the dominant error class is false positives.",
            "There are no false negatives at the default threshold in this run, but that comes with very low precision.",
            "Built-up-area and dense-vegetation radar limitations are plausible hypotheses from the UNOSAT caveat, but this artifact does not prove land-cover causes without an additional land-cover layer.",
        ],
    }


def _describe_group(rows: list[dict]) -> dict:
    probabilities = [float(row["model_probability"]) for row in rows if row["model_probability"] not in {"", None}]
    ndwi_values = [float(row["ndwi_water_fraction"]) for row in rows if row["ndwi_water_fraction"] not in {"", None}]
    lats = [float(row["lat"]) for row in rows]
    lons = [float(row["lon"]) for row in rows]
    return {
        "patches": len(rows),
        "model_probability": _stats(probabilities),
        "ndwi_water_fraction": _stats(ndwi_values),
        "lat_range": [round(min(lats), 6), round(max(lats), 6)] if lats else None,
        "lon_range": [round(min(lons), 6), round(max(lons), 6)] if lons else None,
        "example_patch_ids": [row["patch_id"] for row in rows[:10]],
    }


def _stats(values: list[float]) -> dict | None:
    if not values:
        return None
    return {
        "min": round(min(values), 6),
        "median": round(statistics.median(values), 6),
        "mean": round(statistics.fmean(values), 6),
        "max": round(max(values), 6),
    }


def _buffer_ablation(shapes: list[object], scores: dict[str, dict[str, float]]) -> list[dict]:
    rows = []
    for margin_fraction in [0.0, 0.125, 0.25, 0.375, 0.5]:
        labels = _build_margin_labels(shapes, margin_fraction=margin_fraction)
        matched = [label for label in labels if label.patch_id in scores]
        y_true = np.asarray([label.label for label in matched], dtype=int)
        model_scores = np.asarray([scores[label.patch_id]["model_probability"] for label in matched], dtype=float)
        ndwi_scores = np.asarray([scores[label.patch_id]["ndwi_water_fraction"] for label in matched], dtype=float)
        model_metrics = _metrics(y_true, model_scores, threshold=0.5)
        ndwi_metrics = _metrics(y_true, ndwi_scores, threshold=0.05)
        rows.append(
            {
                "margin_fraction": margin_fraction,
                "flooded_patches": int(y_true.sum()),
                "non_flooded_patches": int(y_true.size - y_true.sum()),
                "model_auc_roc": model_metrics["roc_auc"],
                "model_accuracy": model_metrics["accuracy"],
                "model_precision": model_metrics["precision"],
                "model_recall": model_metrics["recall"],
                "model_f1": model_metrics["f1"],
                "ndwi_auc_roc": ndwi_metrics["roc_auc"],
                "ndwi_f1": ndwi_metrics["f1"],
            }
        )
    return rows


def _build_margin_labels(shapes: list[object], rows: int = 32, cols: int = 32, margin_fraction: float = 0.0) -> list[PatchLabel]:
    min_lon, min_lat, max_lon, max_lat = UNOSAT_BANGLADESH_2024["bbox"]
    indexed_rings = _index_rings(shapes)
    lon_step = (max_lon - min_lon) / cols
    lat_step = (max_lat - min_lat) / rows
    margin_lon = lon_step * margin_fraction
    margin_lat = lat_step * margin_fraction
    candidates: list[list[list[tuple[tuple[float, float, float, float], list[tuple[float, float]]]]]] = [[[] for _col in range(cols)] for _row in range(rows)]
    for bbox, ring in indexed_rings:
        col_start = max(0, int(np.floor((bbox[0] - margin_lon - min_lon) / lon_step)))
        col_end = min(cols - 1, int(np.floor((bbox[2] + margin_lon - min_lon) / lon_step)))
        row_start = max(0, int(np.floor((max_lat - (bbox[3] + margin_lat)) / lat_step)))
        row_end = min(rows - 1, int(np.floor((max_lat - (bbox[1] - margin_lat)) / lat_step)))
        for row in range(row_start, row_end + 1):
            for col in range(col_start, col_end + 1):
                candidates[row][col].append((bbox, ring))

    labels: list[PatchLabel] = []
    for row in range(rows):
        lat = max_lat - (row + 0.5) * lat_step
        for col in range(cols):
            lon = min_lon + (col + 0.5) * lon_step
            offsets = [(0.0, 0.0)]
            if margin_fraction:
                offsets.extend([(margin_lon, 0.0), (-margin_lon, 0.0), (0.0, margin_lat), (0.0, -margin_lat)])
            is_flooded = any(_rings_contain(candidates[row][col], lon + dx, lat + dy) for dx, dy in offsets)
            labels.append(PatchLabel(f"UNOSAT-2024-{row:02d}-{col:02d}", lon, lat, int(is_flooded)))
    return labels


def _write_ablation_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(failure_summary: dict, ablation_rows: list[dict], path: Path) -> None:
    ablation_table = [
        "| Margin | Flooded Patches | Model AUC ROC | Model Accuracy | Model Precision | Model Recall | Model F1 | NDWI AUC ROC | NDWI F1 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in ablation_rows:
        ablation_table.append(
            "| {margin_fraction} | {flooded_patches} | {model_auc_roc} | {model_accuracy} | {model_precision} | {model_recall} | {model_f1} | {ndwi_auc_roc} | {ndwi_f1} |".format(
                **row
            )
        )
    counts = "\n".join(f"- {key}: {value}" for key, value in failure_summary["counts"].items())
    path.write_text(
        "# Bangladesh 2024 Failure Analysis\n\n"
        "These results are computed from real Copernicus Sentinel scores and UNOSAT FL20240825BGD labels.\n\n"
        "## Error Counts\n\n"
        f"{counts}\n\n"
        "## Interpretation\n\n"
        + "\n".join(f"- {item}" for item in failure_summary["interpretation"])
        + "\n\n## Buffer/Margin Ablation\n\n"
        + "\n".join(ablation_table)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
