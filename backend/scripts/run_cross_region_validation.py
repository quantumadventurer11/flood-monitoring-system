from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.cross_region_validation import build_cross_region_report, write_cross_region_outputs  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build cross-region flood validation metrics from real patch-score CSVs.")
    parser.add_argument("--scores-dir", type=Path, default=ROOT / "validation" / "cross_region" / "scores", help="Directory containing per-event real patch-score CSVs.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "validation" / "cross_region", help="Directory for summary JSON/CSV/Markdown outputs.")
    args = parser.parse_args()

    report = build_cross_region_report(args.scores_dir)
    write_cross_region_outputs(report, args.output_dir)

    print(f"Wrote {args.output_dir / 'summary.json'}")
    print(f"Wrote {args.output_dir / 'summary.csv'}")
    print(f"Wrote {args.output_dir / 'summary.md'}")
    print(f"Metric status: {report['metric_status']}")
    print(f"App health: {report['health']['status']}")
    if report["blockers"]:
        print("Blockers:")
        for blocker in report["blockers"]:
            print(f"- {blocker}")


if __name__ == "__main__":
    main()
