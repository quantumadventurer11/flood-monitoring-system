# Bangladesh 2024 Failure Analysis

These results are computed from real Copernicus Sentinel scores and UNOSAT FL20240825BGD labels.

## Error Counts

- false_positive: 953
- true_negative: 39
- true_positive: 32

## Interpretation

- The model over-predicts flood at the default 0.5 threshold: the dominant error class is false positives.
- There are no false negatives at the default threshold in this run, but that comes with very low precision.
- Built-up-area and dense-vegetation radar limitations are plausible hypotheses from the UNOSAT caveat, but this artifact does not prove land-cover causes without an additional land-cover layer.

## Buffer/Margin Ablation

| Margin | Flooded Patches | Model AUC ROC | Model Accuracy | Model Precision | Model Recall | Model F1 | NDWI AUC ROC | NDWI F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 32 | 0.3681 | 0.0693 | 0.0325 | 1.0 | 0.0629 | 0.4232 | 0.0192 |
| 0.125 | 77 | 0.3851 | 0.1133 | 0.0782 | 1.0 | 0.145 | 0.4524 | 0.0474 |
| 0.25 | 93 | 0.4196 | 0.1289 | 0.0944 | 1.0 | 0.1725 | 0.4256 | 0.0372 |
| 0.375 | 100 | 0.4191 | 0.1357 | 0.1015 | 1.0 | 0.1843 | 0.4066 | 0.029 |
| 0.5 | 91 | 0.4617 | 0.127 | 0.0924 | 1.0 | 0.1691 | 0.4179 | 0.0375 |
