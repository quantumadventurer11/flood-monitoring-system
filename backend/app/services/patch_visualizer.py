import math
import random


def ndwi_mask(seed: int = 2024, size: int = 256) -> dict:
    """Generate deterministic raw and masked pixel values for Fig. 2 fallback rendering."""

    rng = random.Random(seed)
    water: list[list[float]] = []
    raw: list[list[list[int]]] = []
    for y in range(size):
        water_row: list[float] = []
        raw_row: list[list[int]] = []
        for x in range(size):
            wave = math.sin(x / 19) + math.cos(y / 23) + math.sin((x + y) / 31)
            ndwi = wave / 3 + rng.uniform(-0.28, 0.18)
            water_row.append(ndwi)
            if ndwi > 0:
                raw_row.append([42 + rng.randrange(25), 96 + rng.randrange(50), 118 + rng.randrange(60)])
            else:
                raw_row.append([92 + rng.randrange(70), 92 + rng.randrange(65), 48 + rng.randrange(45)])
        water.append(water_row)
        raw.append(raw_row)
    return {"size": size, "raw": raw, "ndwi": water}


def patch_grid(seed: int = 2024) -> list[dict]:
    """Return deterministic metadata for 16 simulated patch thumbnails."""

    rng = random.Random(seed)
    patches = []
    for i in range(16):
        flooded = i < 8
        patches.append({"id": i + 1, "label": "FLOOD" if flooded else "NO-FLOOD", "flooded": flooded, "seed": rng.randrange(1_000_000)})
    return patches
