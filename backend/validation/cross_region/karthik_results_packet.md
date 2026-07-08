# Cross-Region Validation Results Packet

Prepared for: Karthik  
Date: 2026-07-08  
Status: Completed real-data cross-region validation metrics

## Executive Summary

The cross-region validation run is complete for Bangladesh 2024, Pakistan 2022, and Mozambique 2023. All three regions use official UNOSAT geospatial flood labels and Copernicus Sentinel-backed model predictions. No fallback proxy predictions were used.

The same 50 km buffer radius is used for each validation region. App health is passing and the final metric table now contains numeric AUC ROC, accuracy, precision, recall, F1, runtime, and patch counts.

## Final Results

| Location | Event Period | 50 km Buffer | Labels | Sentinel Predictions | Patches | AUC ROC | Accuracy | Precision | Recall | F1 | Runtime (s) |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| Bangladesh | 2024-08-28 to 2024-09-04 | Yes | Ready | Copernicus | 35 | 0.7576 | 0.5429 | 0.1111 | 1.0000 | 0.2000 | 245.9402 |
| Pakistan | 2022-08-03 to 2022-08-23 | Yes | Ready | Copernicus | 1024 | 0.5615 | 0.4658 | 0.2500 | 0.6638 | 0.3632 | 4162.4224 |
| Mozambique | 2023-03-11 to 2023-03-15 | Yes | Ready | Copernicus | 1024 | 0.6738 | 0.0518 | 0.0518 | 1.0000 | 0.0984 | 10164.3664 |
| Overall | Combined | Yes | Ready | Copernicus | 2083 | 0.3679 | 0.2636 | 0.1267 | 0.7276 | 0.2157 | 14572.7290 |

## Health Status

| Check | Status |
|---|---|
| References file | Pass |
| Model load | Pass |
| `/health` endpoint | Pass |
| `/model-status` endpoint | Pass |
| `/regions` endpoint | Pass |
| Cross-region metric status | Computed |
| Publishable validation artifacts | True |
| Blockers | None |

## Notes For Interpretation

- These are real validation metrics, not simulated paper-table values.
- The prediction rows are Copernicus Sentinel-backed; fallback proxy predictions were not used.
- The metrics are scientifically honest but not especially strong. Precision is low, especially for Mozambique, which means the current model over-predicts flood in some cross-region settings.
- NDWI remains an audited water signal and is not used as the ground-truth label.
- The validation labels come from official geospatial flood extent products.

## Suggested Paper Wording

Cross-region validation was performed on three historically reported flood events in Bangladesh, Pakistan, and Mozambique using a consistent 50 km validation buffer. Official UNOSAT geospatial flood extent products were converted into patch-level labels, and model probabilities were generated from Copernicus Sentinel-backed preprocessing. The final validation table reports AUC ROC, accuracy, precision, recall, F1, runtime, and patch counts for each region and for the combined evaluation set.

## Message You Can Send

Hi Karthik, I finished the real cross-region validation metrics for Bangladesh 2024, Pakistan 2022, and Mozambique 2023. All three use the same 50 km buffer, official UNOSAT geospatial labels, and Copernicus Sentinel-backed predictions. No fallback/proxy values were used.

The results are:

- Bangladesh: AUC 0.7576, accuracy 0.5429, precision 0.1111, recall 1.0000, F1 0.2000, patches 35.
- Pakistan: AUC 0.5615, accuracy 0.4658, precision 0.2500, recall 0.6638, F1 0.3632, patches 1024.
- Mozambique: AUC 0.6738, accuracy 0.0518, precision 0.0518, recall 1.0000, F1 0.0984, patches 1024.
- Overall: AUC 0.3679, accuracy 0.2636, precision 0.1267, recall 0.7276, F1 0.2157, patches 2083.

The app health checks are passing and the final summary files are ready. The main interpretation is that the current model has high recall but low precision across regions, so it is detecting many floods but also over-predicting flood in several non-flood patches.

## Files

- References: `references`
- Final validation summary: `backend/validation/cross_region/summary.md`
- CSV summary: `backend/validation/cross_region/summary.csv`
- JSON summary: `backend/validation/cross_region/summary.json`
- Ground-truth status: `backend/validation/cross_region/ground_truth_status.json`
- Join status: `backend/validation/cross_region/join_status.json`
