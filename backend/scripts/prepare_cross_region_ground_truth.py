from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.cross_region_validation import VALIDATION_EVENTS  # noqa: E402


SOURCE_AUDITS = {
    "bangladesh_2024": ROOT / "validation" / "audits" / "bangladesh_2024" / "patch_level_audit.csv",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare real cross-region ground-truth label CSVs for validation.")
    parser.add_argument("--source-dir", type=Path, default=ROOT / "validation" / "cross_region" / "official_sources", help="Directory containing official GeoJSON files or zipped shapefiles named by event key.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "validation" / "cross_region" / "labels", help="Directory for prepared label CSVs.")
    parser.add_argument("--status-output", type=Path, default=ROOT / "validation" / "cross_region" / "ground_truth_status.json", help="JSON status output.")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    statuses = []
    for event in VALIDATION_EVENTS:
        if event.key in SOURCE_AUDITS:
            statuses.append(_prepare_from_audit(event, SOURCE_AUDITS[event.key], args.output_dir / event.label_filename))
        elif source_path := _find_official_source(args.source_dir, event.key):
            statuses.append(_prepare_from_official_source(event, source_path, args.output_dir / event.label_filename))
        else:
            statuses.append(
                {
                    "key": event.key,
                    "location": event.location,
                    "status": "source_required",
                    "label_file": str((args.output_dir / event.label_filename).relative_to(ROOT)),
                    "blocker": "Exact authoritative geospatial flood extent file has not been downloaded yet.",
                    "target_ground_truth_source": event.ground_truth_source,
                    "target_ground_truth_url": event.ground_truth_url,
                }
            )

    args.status_output.parent.mkdir(parents=True, exist_ok=True)
    args.status_output.write_text(json.dumps({"events": statuses}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.status_output}")
    for status in statuses:
        print(f"{status['key']}: {status['status']}")


def _prepare_from_audit(event, source_csv: Path, output_csv: Path) -> dict:
    if not source_csv.exists():
        return {
            "key": event.key,
            "location": event.location,
            "status": "source_required",
            "label_file": str(output_csv.relative_to(ROOT)),
            "blocker": f"Missing source audit CSV: {source_csv}",
        }

    min_lon, min_lat, max_lon, max_lat = _buffer_bbox(event.lat, event.lon, event.buffer_km)
    rows = []
    with source_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            lat = float(row["lat"])
            lon = float(row["lon"])
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                rows.append(
                    {
                        "patch_id": f"{event.key}-gt-{len(rows):05d}",
                        "original_patch_id": row["patch_id"],
                        "lat": round(lat, 6),
                        "lon": round(lon, 6),
                        "ground_truth_label": int(float(row["unosat_label"])),
                        "label_source": row["label_source"],
                        "event_date": event.validation_date,
                        "buffer_km": event.buffer_km,
                        "scene_bounds": f"{min_lon},{min_lat},{max_lon},{max_lat}",
                    }
                )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["patch_id", "original_patch_id", "lat", "lon", "ground_truth_label", "label_source", "event_date", "buffer_km", "scene_bounds"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    flooded = sum(int(row["ground_truth_label"]) for row in rows)
    return {
        "key": event.key,
        "location": event.location,
        "status": "ready" if rows else "empty",
        "label_file": str(output_csv.relative_to(ROOT)),
        "patches": len(rows),
        "flooded_patches": flooded,
        "non_flooded_patches": len(rows) - flooded,
        "buffer_km": event.buffer_km,
        "source": str(source_csv.relative_to(ROOT)),
        "blocker": None if rows else "No source audit rows fell inside the configured 50 km validation buffer.",
    }


def _prepare_from_official_source(event, source_path: Path, output_csv: Path) -> dict:
    polygons = _load_polygons(source_path)
    min_lon, min_lat, max_lon, max_lat = _buffer_bbox(event.lat, event.lon, event.buffer_km)
    rows = []
    grid_rows = 32
    grid_cols = 32
    lon_step = (max_lon - min_lon) / grid_cols
    lat_step = (max_lat - min_lat) / grid_rows
    for row_index in range(grid_rows):
        lat = max_lat - (row_index + 0.5) * lat_step
        for col_index in range(grid_cols):
            lon = min_lon + (col_index + 0.5) * lon_step
            flooded = any(_point_in_polygon(lon, lat, polygon) for polygon in polygons)
            rows.append(
                {
                    "patch_id": f"{event.key}-gt-{row_index:02d}-{col_index:02d}",
                    "original_patch_id": "",
                    "lat": round(lat, 6),
                    "lon": round(lon, 6),
                    "ground_truth_label": int(flooded),
                    "label_source": event.ground_truth_source,
                    "event_date": event.validation_date,
                    "buffer_km": event.buffer_km,
                    "scene_bounds": f"{min_lon},{min_lat},{max_lon},{max_lat}",
                }
            )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["patch_id", "original_patch_id", "lat", "lon", "ground_truth_label", "label_source", "event_date", "buffer_km", "scene_bounds"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    flooded = sum(int(row["ground_truth_label"]) for row in rows)
    return {
        "key": event.key,
        "location": event.location,
        "status": "ready" if 0 < flooded < len(rows) else "needs_review",
        "label_file": str(output_csv.relative_to(ROOT)),
        "patches": len(rows),
        "flooded_patches": flooded,
        "non_flooded_patches": len(rows) - flooded,
        "buffer_km": event.buffer_km,
        "source": str(source_path.relative_to(ROOT)) if source_path.is_relative_to(ROOT) else str(source_path),
        "blocker": None if 0 < flooded < len(rows) else "Official source loaded, but the 50 km grid does not contain both flooded and non-flooded labels.",
    }


def _buffer_bbox(lat: float, lon: float, buffer_km: float) -> tuple[float, float, float, float]:
    lat_delta = buffer_km / 111.32
    lon_delta = buffer_km / max(1e-6, 111.32 * math.cos(math.radians(lat)))
    return lon - lon_delta, lat - lat_delta, lon + lon_delta, lat + lat_delta


def _find_official_source(source_dir: Path, key: str) -> Path | None:
    candidates = [
        source_dir / f"{key}.geojson",
        source_dir / f"{key}.json",
        source_dir / f"{key}.zip",
        source_dir / key / f"{key}.geojson",
        source_dir / key / f"{key}.json",
        source_dir / key / f"{key}.zip",
    ]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def _load_polygons(path: Path) -> list[list[tuple[float, float]]]:
    if path.suffix.lower() in {".geojson", ".json"}:
        return _load_geojson_polygons(path)
    if path.suffix.lower() == ".zip":
        return _load_zipped_shapefile_polygons(path)
    raise ValueError(f"Unsupported official source format: {path}")


def _load_geojson_polygons(path: Path) -> list[list[tuple[float, float]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", []) if payload.get("type") == "FeatureCollection" else [{"geometry": payload.get("geometry", payload)}]
    polygons: list[list[tuple[float, float]]] = []
    for feature in features:
        geometry = feature.get("geometry") or {}
        polygons.extend(_rings_from_geometry(geometry))
    return polygons


def _rings_from_geometry(geometry: dict) -> list[list[tuple[float, float]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    if geometry_type == "Polygon":
        return [_ring_to_points(ring) for ring in coordinates[:1]]
    if geometry_type == "MultiPolygon":
        rings = []
        for polygon in coordinates:
            rings.extend(_ring_to_points(ring) for ring in polygon[:1])
        return rings
    return []


def _ring_to_points(ring: list) -> list[tuple[float, float]]:
    return [(float(point[0]), float(point[1])) for point in ring]


def _load_zipped_shapefile_polygons(path: Path) -> list[list[tuple[float, float]]]:
    try:
        import shapefile  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - CLI dependency guard.
        raise RuntimeError("Install pyshp to read official zipped shapefiles: pip install pyshp") from exc

    import io

    with zipfile.ZipFile(path) as archive:
        base = _select_shapefile_base(archive, path)
        members = {suffix: f"{base}{suffix}" for suffix in [".shp", ".shx", ".dbf"]}
        missing = {".shp", ".shx", ".dbf"} - members.keys()
        if missing:
            raise FileNotFoundError(f"{path} is missing shapefile member(s): {', '.join(sorted(missing))}")
        reader = shapefile.Reader(
            shp=io.BytesIO(archive.read(members[".shp"])),
            shx=io.BytesIO(archive.read(members[".shx"])),
            dbf=io.BytesIO(archive.read(members[".dbf"])),
        )
        polygons = []
        for shape in reader.shapes():
            points = [(float(x), float(y)) for x, y in shape.points]
            parts = list(shape.parts) + [len(points)]
            for start, end in zip(parts[:-1], parts[1:], strict=True):
                ring = points[start:end]
                if len(ring) >= 3:
                    polygons.append(ring)
        return polygons


def _select_shapefile_base(archive: zipfile.ZipFile, source_path: Path) -> str:
    suffixes = {".shp", ".shx", ".dbf"}
    grouped: dict[str, set[str]] = {}
    for name in archive.namelist():
        suffix = Path(name).suffix.lower()
        if suffix in suffixes:
            grouped.setdefault(name[: -len(suffix)], set()).add(suffix)

    complete = [base for base, available in grouped.items() if suffixes.issubset(available)]
    if not complete:
        raise FileNotFoundError(f"{source_path} does not contain a complete shapefile")

    source_name = source_path.name.lower()
    preferred_tokens: list[str] = []
    if "pakistan_2022" in source_name:
        preferred_tokens = ["viirs_20220803_20220823_floodextent_pak"]
    elif "mozambique_2023" in source_name:
        preferred_tokens = ["rcm2_20230313_zambezia_floodextent"]

    def score(base: str) -> tuple[int, str]:
        lower = base.lower()
        value = 0
        if any(token in lower for token in preferred_tokens):
            value += 1000
        if "floodextent" in lower:
            value += 100
        if "waterextent" in lower:
            value += 50
        if "analysisextent" in lower or "cloudobstruction" in lower:
            value -= 100
        return value, lower

    return max(complete, key=score)


def _point_in_polygon(lon: float, lat: float, ring: list[tuple[float, float]]) -> bool:
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


if __name__ == "__main__":
    main()
