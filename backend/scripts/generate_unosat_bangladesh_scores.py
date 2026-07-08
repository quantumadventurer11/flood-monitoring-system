from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import date
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services import satellite  # noqa: E402
from app.services.classifier import MODEL_FEATURE_INDICES, predict  # noqa: E402
from app.services.independent_validation import (  # noqa: E402
    UNOSAT_BANGLADESH_2024,
    build_patch_labels,
    download_unosat_shapefile,
    load_unosat_shapes,
)
from app.services.preprocessing import preprocess_scene  # noqa: E402


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Generate real Sentinel-backed scores for the UNOSAT Bangladesh 2024 32x32 validation grid.")
    parser.add_argument("--output", type=Path, default=ROOT / "validation" / "bangladesh_2024_real_scores.csv")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".validation_cache")
    args = parser.parse_args()

    if not satellite.credentials_available():
        raise SystemExit("Copernicus credentials are not configured. Refusing to generate fallback-derived validation scores.")

    zip_path = download_unosat_shapefile(args.cache_dir / "FL20240825BGD_SHP.zip")
    labels = build_patch_labels(load_unosat_shapes(zip_path))
    min_lon, min_lat, max_lon, max_lat = UNOSAT_BANGLADESH_2024["bbox"]
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    north_south_km = (max_lat - min_lat) * 111.32 / 2
    east_west_km = (max_lon - min_lon) * 111.32 * abs(math.cos(math.radians(center_lat))) / 2
    buffer_km = max(north_south_km, east_west_km) + 10

    satellite.VALIDATION_RASTER_SHAPE = (2048, 2048)
    started = time.perf_counter()
    print(
        "Fetching Copernicus Sentinel scene for UNOSAT Bangladesh grid "
        f"center=({center_lat:.6f},{center_lon:.6f}), buffer_km={buffer_km:.1f}",
        flush=True,
    )
    scene = await satellite.fetch_satellite_scene(
        "Bangladesh",
        center_lat,
        center_lon,
        buffer_km,
        date.fromisoformat("2024-08-18"),
        date.fromisoformat("2024-09-04"),
    )
    if scene.get("source") != "copernicus":
        raise RuntimeError(f"Expected Copernicus Sentinel scene, got {scene.get('source')}")

    print(f"Preprocessing Sentinel scene dated {scene.get('date')}", flush=True)
    records = preprocess_scene(scene, patch_size=64)
    if len(records) < len(labels):
        raise RuntimeError(f"Expected at least {len(labels)} Sentinel patch records, got {len(records)}")
    records = records[: len(labels)]
    elapsed = time.perf_counter() - started

    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(f"Scoring {len(records)} patches with NDWI-free model", flush=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["patch_id", "ndwi_water_fraction", "model_probability", "data_source", "scene_date", "runtime_seconds", "model_feature_count"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, (label, record) in enumerate(zip(labels, records, strict=True)):
            result = predict(record["features"])
            writer.writerow(
                {
                    "patch_id": label.patch_id,
                    "ndwi_water_fraction": round(float(record["ndwi_water_fraction"]), 6),
                    "model_probability": result["flood_probability"],
                    "data_source": scene["source"],
                    "scene_date": scene["date"],
                    "runtime_seconds": round(elapsed, 4) if index == 0 else 0.0,
                    "model_feature_count": len(MODEL_FEATURE_INDICES),
                }
            )
    print(f"Wrote {args.output}")
    print(f"Patch scores: {len(records)}")
    print(f"Model feature count: {len(MODEL_FEATURE_INDICES)}")
    print(f"Runtime seconds: {elapsed:.4f}")


if __name__ == "__main__":
    asyncio.run(main_async())
