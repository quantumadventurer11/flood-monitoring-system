from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import date, timedelta
import math
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.classifier import predict  # noqa: E402
from app.services.cross_region_validation import VALIDATION_EVENTS  # noqa: E402
from app.services.preprocessing import preprocess_scene  # noqa: E402
from app.services.satellite import credentials_available, fetch_satellite_scene  # noqa: E402


async def main_async() -> None:
    parser = argparse.ArgumentParser(description="Generate Sentinel-backed model predictions for cross-region validation.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "validation" / "cross_region" / "predictions", help="Directory for prediction CSVs.")
    parser.add_argument("--lookback-days", type=int, default=14, help="Days before the validation date to search for Sentinel products.")
    parser.add_argument("--lookahead-days", type=int, default=3, help="Days after the validation date to search for Sentinel products.")
    parser.add_argument("--event-key", choices=[event.key for event in VALIDATION_EVENTS], help="Generate predictions for one validation event only.")
    parser.add_argument("--allow-fallback", action="store_true", help="Allow fallback proxy output for debugging only; never publish these metrics.")
    args = parser.parse_args()

    if not credentials_available() and not args.allow_fallback:
        raise SystemExit("Copernicus credentials are not configured. Refusing to generate validation predictions from fallback proxy data.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    events = [event for event in VALIDATION_EVENTS if args.event_key in {None, event.key}]
    for event in events:
        output_path = args.output_dir / event.prediction_filename
        result = await _generate_event_predictions(event, output_path, lookback_days=args.lookback_days, lookahead_days=args.lookahead_days, allow_fallback=args.allow_fallback)
        print(f"{event.key}: {result}", flush=True)


async def _generate_event_predictions(event, output_path: Path, lookback_days: int, lookahead_days: int, allow_fallback: bool) -> str:
    target_date = date.fromisoformat(event.validation_date)
    started = time.perf_counter()
    print(
        f"{event.key}: fetching Sentinel scene for {event.validation_date} "
        f"({lookback_days} days back, {lookahead_days} days ahead)",
        flush=True,
    )
    scene = await fetch_satellite_scene(event.location, event.lat, event.lon, event.buffer_km, target_date - timedelta(days=lookback_days), target_date + timedelta(days=lookahead_days))
    if scene.get("source") != "copernicus" and not allow_fallback:
        raise RuntimeError(f"{event.key} did not return Copernicus data; got {scene.get('source')}")

    print(f"{event.key}: preprocessing Sentinel scene", flush=True)
    records = preprocess_scene(scene)
    elapsed = time.perf_counter() - started
    centroids = _patch_centroids(len(records), event.lat, event.lon, event.buffer_km)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"{event.key}: scoring {len(records)} patches", flush=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["patch_id", "lat", "lon", "model_probability", "ndwi_water_fraction", "runtime_seconds", "data_source", "event_date", "buffer_km"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, record in enumerate(records):
            result = predict(record["features"])
            lat, lon = centroids[index]
            writer.writerow(
                {
                    "patch_id": f"{event.key}-pred-{index:05d}",
                    "lat": lat,
                    "lon": lon,
                    "model_probability": result["flood_probability"],
                    "ndwi_water_fraction": round(float(record["ndwi_water_fraction"]), 6),
                    "runtime_seconds": round(elapsed, 4) if index == 0 else 0.0,
                    "data_source": scene.get("source"),
                    "event_date": event.validation_date,
                    "buffer_km": event.buffer_km,
                }
            )
    return f"wrote {len(records)} predictions to {output_path.relative_to(ROOT)}"


def _patch_centroids(count: int, center_lat: float, center_lon: float, buffer_km: float) -> list[tuple[float, float]]:
    cols = max(1, int(math.sqrt(count)))
    rows = math.ceil(count / cols)
    lat_radius = buffer_km / 111.0
    lon_radius = buffer_km / max(1e-6, 111.0 * math.cos(math.radians(center_lat)))
    min_lat, max_lat = center_lat - lat_radius, center_lat + lat_radius
    min_lon, max_lon = center_lon - lon_radius, center_lon + lon_radius
    lat_step = (max_lat - min_lat) / rows
    lon_step = (max_lon - min_lon) / cols
    centroids = []
    for index in range(count):
        row = index // cols
        col = index % cols
        centroids.append((round(max_lat - (row + 0.5) * lat_step, 6), round(min_lon + (col + 0.5) * lon_step, 6)))
    return centroids


if __name__ == "__main__":
    asyncio.run(main_async())
