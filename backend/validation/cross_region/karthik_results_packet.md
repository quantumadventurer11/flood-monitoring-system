# Cross-Region Validation Results Packet

Prepared for: Karthik  
Date: 2026-07-06  
Status: Forwardable progress packet, not final publishable metrics

## Executive Summary

The cross-region validation pipeline is now set up for three historically reported flood events: Bangladesh 2024, Pakistan 2022, and Mozambique 2023. The same 50 km buffer radius is used for all validation regions.

Current system health is passing. The backend health endpoint, model-status endpoint, model loading check, and regions endpoint are all healthy.

Final metrics are still pending because real Sentinel-backed prediction CSVs and final joined score CSVs are not available yet. No fake AUC ROC, accuracy, precision, recall, F1, runtime, or patch-count metrics have been generated.

## Current Results Readiness

| Location | Event Period | 50 km Buffer | References | Ground-Truth Labels | Sentinel Predictions | Final Metrics |
|---|---|---:|---|---|---|---|
| Bangladesh | 2024-08-28 to 2024-09-04 | Yes | Ready | Ready: 35 labels, 2 flooded, 33 non-flooded | Missing | `scores_required` |
| Pakistan | 2022-08-03 to 2022-08-23 | Yes | Ready | Missing authoritative geospatial flood extent file | Missing | `scores_required` |
| Mozambique | 2023-03-11 to 2023-03-15 | Yes | Ready | Missing authoritative geospatial flood extent file | Missing | `scores_required` |

## Health Status

| Check | Status |
|---|---|
| References file | Pass |
| Model load | Pass |
| `/health` endpoint | Pass |
| `/model-status` endpoint | Pass |
| `/regions` endpoint | Pass |
| Backend tests | Pass: 27 passed |

## Metrics Status

The following metrics are ready to be computed once the real patch-score CSVs are available:

- AUC ROC: `TBD`
- Accuracy: `TBD`
- Precision: `TBD`
- Recall: `TBD`
- F1: `TBD`
- Runtime: `TBD`
- Number of patches used: `TBD`

The validation script expects final score CSVs in:

```text
backend/validation/cross_region/scores/
```

Required final score files:

```text
bangladesh_2024_patch_scores.csv
pakistan_2022_patch_scores.csv
mozambique_2023_patch_scores.csv
```

Each final score CSV must include:

```text
patch_id,ground_truth_label,model_probability,ndwi_water_fraction,lat,lon,runtime_seconds
```

To create those files after official labels and Copernicus prediction CSVs are available, run:

```text
python scripts\join_cross_region_scores.py
```

## Current Blockers

1. Pakistan 2022 and Mozambique 2023 still need exact authoritative geospatial flood extent files from UNOSAT, Copernicus EMS, or an equivalent official source.
2. Copernicus credentials are not configured, so Sentinel-backed prediction CSVs cannot be generated yet.
3. Final score CSVs are missing because labels and Sentinel predictions have not yet been spatially joined.

The Sentinel prediction script intentionally refuses fallback proxy data. This protects the paper from reporting non-publishable validation metrics.

## Immediate External Inputs Needed

1. Create or obtain Copernicus Data Space credentials and add them to `backend/.env`:

```text
COPERNICUS_USER=...
COPERNICUS_PASSWORD=...
```

2. Request official Pakistan and Mozambique flood extent files using:

```text
backend/validation/cross_region/official_data_request.md
```

3. Place returned files in:

```text
backend/validation/cross_region/official_sources/
```

## GLOC 2026 Readiness Notes

What is ready:

- Cross-region validation structure.
- Historical references for all three events.
- Same 50 km buffer radius across regions.
- Bangladesh ground-truth labels from UNOSAT-derived validation data.
- Health checks and backend tests.

What is not ready yet:

- Final cross-region performance table.
- Pakistan and Mozambique geospatial label CSVs.
- Sentinel-backed model probability CSVs.
- Final joined score CSVs.
- Publishable AUC ROC, accuracy, precision, recall, F1, runtime, and patch-count values.

## Suggested Paper Wording

The cross-region validation framework was prepared using historically reported flood events in Bangladesh, Pakistan, and Mozambique. A consistent 50 km validation buffer was applied across all regions. Independent flood extent products are treated as ground-truth labels, while NDWI remains a model feature rather than the validation label. Final quantitative metrics will be reported only after Sentinel-backed model predictions are spatially joined with independent geospatial flood labels.

## Message You Can Send

Hi Karthik, I prepared the cross-region validation results packet. The pipeline is ready, references are saved, and we are using the same 50 km buffer for Bangladesh, Pakistan, and Mozambique. Bangladesh ground-truth labels are prepared from the UNOSAT-derived validation data. The app health checks and backend tests are passing.

The final metrics are still pending because we need real Sentinel-backed prediction CSVs and authoritative geospatial flood extent files for Pakistan and Mozambique. I did not generate fake values. Once those inputs are available, the system will compute AUC ROC, accuracy, precision, recall, F1, runtime, and patch counts automatically.

## Files

- References: `references`
- Validation summary: `backend/validation/cross_region/summary.md`
- Ground-truth status: `backend/validation/cross_region/ground_truth_status.json`
- CSV summary: `backend/validation/cross_region/summary.csv`
- Join status: `backend/validation/cross_region/join_status.json`
