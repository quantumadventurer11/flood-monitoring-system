from datetime import date, timedelta
import io
import logging
import math
from pathlib import Path
import tempfile
import zipfile

import httpx
import numpy as np
import rasterio
from rasterio.enums import Resampling

from app.config import get_settings


logger = logging.getLogger(__name__)
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
DOWNLOAD_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/era5"


def credentials_available() -> bool:
    settings = get_settings()
    return bool(settings.copernicus_user and settings.copernicus_password)


def _bbox(lat: float, lon: float, buffer_km: float) -> tuple[float, float, float, float]:
    lat_delta = buffer_km / 111.32
    lon_delta = buffer_km / max(1e-6, 111.32 * math.cos(math.radians(lat)))
    return lon - lon_delta, lat - lat_delta, lon + lon_delta, lat + lat_delta


def _polygon_wkt(lat: float, lon: float, buffer_km: float) -> str:
    min_lon, min_lat, max_lon, max_lat = _bbox(lat, lon, buffer_km)
    return f"POLYGON(({min_lon} {min_lat},{max_lon} {min_lat},{max_lon} {max_lat},{min_lon} {max_lat},{min_lon} {min_lat}))"


async def _token(client: httpx.AsyncClient) -> str:
    settings = get_settings()
    response = await client.post(
        TOKEN_URL,
        data={
            "client_id": "cdse-public",
            "grant_type": "password",
            "username": settings.copernicus_user,
            "password": settings.copernicus_password,
        },
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


async def _search_products(client: httpx.AsyncClient, collection: str, product_filter: str, lat: float, lon: float, buffer_km: float, start_date: date, end_date: date, top: int = 1) -> list[dict]:
    start = start_date.isoformat() + "T00:00:00.000Z"
    end = (end_date + timedelta(days=1)).isoformat() + "T00:00:00.000Z"
    polygon = _polygon_wkt(lat, lon, buffer_km)
    filters = [
        f"Collection/Name eq '{collection}'",
        f"ContentDate/Start ge {start}",
        f"ContentDate/Start lt {end}",
        f"OData.CSC.Intersects(area=geography'SRID=4326;{polygon}')",
        product_filter,
    ]
    if collection == "SENTINEL-2":
        filters.append("Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt 30)")
    params = {"$filter": " and ".join(filters), "$orderby": "ContentDate/Start desc", "$top": str(top)}
    response = await client.get(CATALOGUE_URL, params=params)
    response.raise_for_status()
    return list(response.json().get("value", []))


async def _download_zip(client: httpx.AsyncClient, token: str, product_id: str) -> bytes:
    response = await client.get(DOWNLOAD_URL.format(product_id=product_id), headers={"Authorization": f"Bearer {token}"}, follow_redirects=True, timeout=180)
    response.raise_for_status()
    return bytes(response.content)


def _find_member(zf: zipfile.ZipFile, candidates: list[str]) -> str:
    names = zf.namelist()
    lower = [(name, name.lower()) for name in names]
    for token in candidates:
        token_l = token.lower()
        matches = [name for name, low in lower if token_l in low and not low.endswith("/")]
        if matches:
            return sorted(matches, key=len)[0]
    raise FileNotFoundError(f"No ZIP member matched {candidates}")


def _read_zip_raster(zf: zipfile.ZipFile, member: str, out_shape: tuple[int, int] | None = None) -> np.ndarray:
    suffix = Path(member).suffix or ".tif"
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(zf.read(member))
        tmp.flush()
        with rasterio.open(tmp.name) as src:
            if out_shape:
                arr = src.read(1, out_shape=out_shape, resampling=Resampling.bilinear)
            else:
                arr = src.read(1)
    return np.asarray(arr, dtype=float)


def _extract_s2(zip_bytes: bytes) -> dict[str, np.ndarray]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        b03_member = _find_member(zf, ["_B03_10m.jp2", "_B03.jp2", "B03_10m"])
        b04_member = _find_member(zf, ["_B04_10m.jp2", "_B04.jp2", "B04_10m"])
        b08_member = _find_member(zf, ["_B08_10m.jp2", "_B08.jp2", "B08_10m"])
        b03 = _read_zip_raster(zf, b03_member)
        target_shape = b03.shape
        b04 = _read_zip_raster(zf, b04_member, target_shape)
        b08 = _read_zip_raster(zf, b08_member, target_shape)
        try:
            qa_member = _find_member(zf, ["_QA60_60m.jp2", "_QA60.jp2", "QA60"])
            qa60 = _read_zip_raster(zf, qa_member, target_shape).astype(np.uint16)
        except FileNotFoundError:
            qa60 = np.zeros(target_shape, dtype=np.uint16)
    return {"B03": b03, "B04": b04, "B08": b08, "QA60": qa60}


def _extract_s1_vv(zip_bytes: bytes, target_shape: tuple[int, int]) -> np.ndarray:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        vv_member = _find_member(zf, ["measurement", "-vv-", "_vv_", "vv"])
        return _read_zip_raster(zf, vv_member, target_shape)


def _fit_common(scene: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    height = min(arr.shape[0] for arr in scene.values())
    width = min(arr.shape[1] for arr in scene.values())
    return {key: value[:height, :width] for key, value in scene.items()}


async def _open_meteo_fallback(lat: float, lon: float, target_date: date) -> dict:
    """Create satellite-like arrays from ERA5 precipitation and a conservative moisture prior."""

    rain_7d = 0.0
    max_daily_rain = 0.0
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            start_date = target_date - timedelta(days=6)
            response = await client.get(
                OPEN_METEO_ARCHIVE_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "start_date": start_date.isoformat(),
                    "end_date": target_date.isoformat(),
                    "daily": "precipitation_sum",
                    "timezone": "auto",
                },
            )
            response.raise_for_status()
            payload = response.json()
            daily_rain = [float(value or 0.0) for value in payload.get("daily", {}).get("precipitation_sum", [])]
            if daily_rain:
                rain_7d = float(np.sum(daily_rain))
                max_daily_rain = float(np.max(daily_rain))
    except Exception as exc:
        logger.warning("Open-Meteo satellite fallback failed: %s", exc)

    rng = np.random.default_rng(abs(hash((round(lat, 3), round(lon, 3), target_date.isoformat()))) % (2**32))
    size = 256
    yy, xx = np.mgrid[0:size, 0:size]
    prior = _surface_water_prior(lat, lon)
    water_signal = float(np.clip(prior + rain_7d / 220 + max_daily_rain / 180, 0.0, 0.92))
    basin = np.exp(-(((xx - size * 0.45) / 70) ** 2 + ((yy - size * 0.52) / 42) ** 2))
    river = np.exp(-((yy - size * 0.62 - np.sin(xx / 23) * 24) ** 2) / 900)
    floodplain = basin * 0.35 + river * 0.45 + rng.normal(0, 0.05, (size, size))
    threshold = 0.82 - water_signal * 0.55
    water = floodplain > threshold
    b03 = 0.22 + water * 0.34 + rng.normal(0, 0.035, (size, size))
    b04 = 0.26 + water * 0.08 + rng.normal(0, 0.03, (size, size))
    b08 = 0.48 - water * 0.34 + rng.normal(0, 0.04, (size, size))
    vv = -14 + water * -5 + rng.normal(0, 1.8, (size, size))
    qa60 = np.zeros((size, size), dtype=np.uint16)
    return {
        "B03": b03,
        "B04": b04,
        "B08": b08,
        "VV": vv,
        "QA60": qa60,
        "source": "fallback",
        "date": target_date.isoformat(),
        "lat": lat,
        "lon": lon,
        "rain_7d_mm": round(rain_7d, 2),
        "max_daily_rain_mm": round(max_daily_rain, 2),
        "water_signal": round(water_signal, 4),
    }


def _surface_water_prior(lat: float, lon: float) -> float:
    """Approximate standing-water likelihood when no live satellite tile is available."""

    # Known arid belts should not produce synthetic flood water without rainfall.
    if 15 <= lat <= 32 and -18 <= lon <= 36:
        return 0.0
    if -30 <= lat <= -15 and -75 <= lon <= -65:
        return 0.0
    if -32 <= lat <= -15 and 120 <= lon <= 145:
        return 0.02

    # River deltas and low wetland regions get a modest prior, but still need rain for High risk.
    if 20 <= lat <= 27 and 88 <= lon <= 93:
        return 0.18
    if 49 <= lat <= 54 and 3 <= lon <= 8:
        return 0.12
    if -5 <= lat <= 8 and -75 <= lon <= -45:
        return 0.12
    if 5 <= lat <= 15 and 28 <= lon <= 36:
        return 0.14
    return 0.06


async def fetch_satellite_scene(country: str, lat: float, lon: float, buffer_km: float, start_date: date, end_date: date) -> dict:
    """Fetch Sentinel-1/2 scene arrays, falling back to Open-Meteo proxy arrays."""

    target_date = end_date
    if not credentials_available():
        logger.warning("Copernicus credentials missing; using Open-Meteo fallback for %s", country)
        return await _open_meteo_fallback(lat, lon, target_date)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            token = await _token(client)
            s2 = await _search_products(
                client,
                "SENTINEL-2",
                "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')",
                lat,
                lon,
                buffer_km,
                start_date,
                end_date,
            )
            s1 = await _search_products(
                client,
                "SENTINEL-1",
                "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and contains(att/OData.CSC.StringAttribute/Value,'GRD'))",
                lat,
                lon,
                buffer_km,
                start_date,
                end_date,
            )
            if not s2 or not s1:
                raise RuntimeError("No matching Sentinel-1/Sentinel-2 products found")
            s2_zip = await _download_zip(client, token, s2[0]["Id"])
            s1_zip = await _download_zip(client, token, s1[0]["Id"])

        s2_bands = _extract_s2(s2_zip)
        vv = _extract_s1_vv(s1_zip, s2_bands["B03"].shape)
        scene = _fit_common({**s2_bands, "VV": vv})
        scene.update(
            {
                "source": "copernicus",
                "date": str(s2[0].get("ContentDate", {}).get("Start", end_date.isoformat()))[:10],
                "lat": lat,
                "lon": lon,
            }
        )
        return scene
    except Exception as exc:
        logger.warning("Copernicus satellite fetch failed for %s; using fallback: %s", country, exc)
        return await _open_meteo_fallback(lat, lon, target_date)


async def ingest_sentinel_scene(country: str, lat: float, lon: float, buffer_km: float, start_date: date, end_date: date) -> dict:
    """Fetch and lightly validate a Sentinel scene for ingest requests."""

    scene = await fetch_satellite_scene(country, lat, lon, buffer_km, start_date, end_date)
    patches_processed = int((scene["B03"].shape[0] // 64) * (scene["B03"].shape[1] // 64))
    return {"status": scene["source"], "patches_processed": patches_processed}
