import numpy as np
from scipy.stats import kurtosis, skew
from skimage.feature import graycomatrix, graycoprops


def apply_qa60_cloud_mask(bands: dict[str, np.ndarray], qa60: np.ndarray) -> dict[str, np.ndarray]:
    """Mask Sentinel-2 cloud-contaminated pixels using QA60 cloud bits."""

    cloud_bits = (1 << 10) | (1 << 11)
    clear = (qa60.astype(np.uint16) & cloud_bits) == 0
    return {name: np.where(clear, values, np.nan) for name, values in bands.items()}


def normalized_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    denom = a + b
    return np.divide(a - b, denom, out=np.zeros_like(a, dtype=float), where=np.abs(denom) > 1e-9)


def compute_indices(b3: np.ndarray, b4: np.ndarray, b8: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return NDWI and NDVI arrays from Sentinel-2 green, red, and NIR bands."""

    ndwi = normalized_difference(b3, b8)
    ndvi = normalized_difference(b8, b4)
    return ndwi, ndvi


def normalize_to_unit(values: np.ndarray) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.zeros_like(values, dtype=float)
    lo, hi = np.nanpercentile(finite, [1, 99])
    if np.isclose(lo, hi):
        return np.zeros_like(values, dtype=float)
    clipped = np.clip(values, lo, hi)
    return 2 * ((clipped - lo) / (hi - lo)) - 1


def tile_patches(stack: np.ndarray, patch_size: int = 64) -> list[np.ndarray]:
    """Tile a channel-first image stack into non-overlapping patches."""

    channels, height, width = stack.shape
    patches: list[np.ndarray] = []
    for y in range(0, height - patch_size + 1, patch_size):
        for x in range(0, width - patch_size + 1, patch_size):
            patches.append(stack[:, y : y + patch_size, x : x + patch_size])
    return patches


def _band_features(values: np.ndarray) -> list[float]:
    finite = values[np.isfinite(values)].astype(float)
    if finite.size == 0:
        finite = np.array([0.0])
    stats = [
        np.mean(finite),
        np.std(finite),
        np.min(finite),
        np.max(finite),
        np.median(finite),
        skew(finite, bias=False) if finite.size > 2 else 0.0,
        kurtosis(finite, bias=False) if finite.size > 3 else 0.0,
        *np.percentile(finite, [5, 25, 75, 95]).tolist(),
    ]
    scaled = np.nan_to_num(((values + 1) * 127.5), nan=0.0, posinf=255.0, neginf=0.0)
    scaled = np.clip(scaled, 0, 255).astype(np.uint8)
    glcm = graycomatrix(scaled, distances=[1], angles=[0], levels=256, symmetric=True, normed=True)
    texture = [float(graycoprops(glcm, prop)[0, 0]) for prop in ["contrast", "homogeneity", "energy", "correlation"]]
    return [float(np.nan_to_num(v)) for v in [*stats, *texture]]


def extract_patch_features(patch: np.ndarray, ndwi_band_index: int = 3) -> list[float]:
    """Extract 61 engineered features from a 4-band 64x64 patch."""

    features: list[float] = []
    for band in patch:
        features.extend(_band_features(band))
    water_fraction = float(np.nanmean(patch[ndwi_band_index] > 0.0))
    features.append(water_fraction)
    return features


def label_patch(patch: np.ndarray, ndwi_band_index: int = 3, flood_fraction_threshold: float = 0.05) -> int:
    """Return 1 when more than 5% of pixels have NDWI > 0.0."""

    return int(float(np.nanmean(patch[ndwi_band_index] > 0.0)) > flood_fraction_threshold)
