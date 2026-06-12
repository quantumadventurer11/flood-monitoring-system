from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.independent_validation import (  # noqa: E402
    build_patch_labels,
    download_unosat_shapefile,
    load_unosat_shapes,
    read_score_csv,
    summarize_validation,
    write_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate patch-level flood scores against UNOSAT FL20240825BGD.")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".validation_cache", help="Directory for downloaded UNOSAT ZIP files.")
    parser.add_argument("--scores-csv", type=Path, help="CSV with patch_id, ndwi_water_fraction, and model_probability columns.")
    parser.add_argument("--output", type=Path, default=ROOT / "validation" / "unosat_bangladesh_2024_summary.json", help="Output JSON path.")
    args = parser.parse_args()

    zip_path = download_unosat_shapefile(args.cache_dir / "FL20240825BGD_SHP.zip")
    shapes = load_unosat_shapes(zip_path)
    labels = build_patch_labels(shapes)
    scores = read_score_csv(args.scores_csv) if args.scores_csv else None
    summary = summarize_validation(labels, scores)
    write_summary(summary, args.output)
    print(f"Wrote {args.output}")
    print(f"Metric status: {summary['metric_status']}")
    print(f"Ground-truth patches: {summary['ground_truth']['patches']}")
    print(f"Flooded patches: {summary['ground_truth']['flooded_patches']} ({summary['ground_truth']['flooded_percent']}%)")


if __name__ == "__main__":
    main()
