PAPER_RESULTS = {
    "dataset_stats": [
        {"month": "June", "date": "2024-06-01", "total_patches": 2630, "flooded_percent": 41.8},
        {"month": "July", "date": "2024-07-01", "total_patches": 2249, "flooded_percent": 13.3},
        {"month": "August", "date": "2024-08-01", "total_patches": 1889, "flooded_percent": 3.9},
    ],
    "model_metrics": [
        {"rank": 1, "model": "XGBoost", "roc_auc": 0.9985, "accuracy": "99.4%", "precision": "86.7%", "recall": "98.6%", "f1": 0.923, "training_time_s": 0.2},
        {"rank": 2, "model": "Simple CNN", "roc_auc": 0.9982, "accuracy": "99.0%", "precision": "82.9%", "recall": "93.2%", "f1": 0.877},
        {"rank": 3, "model": "Logistic Regression", "roc_auc": 0.9978, "accuracy": "99.2%", "precision": "85.2%", "recall": "94.5%", "f1": 0.896},
        {"rank": 4, "model": "Random Forest", "roc_auc": 0.9976, "accuracy": "99.1%", "precision": "84.1%", "recall": "94.5%", "f1": 0.890},
        {"rank": 5, "model": "SVM (RBF)", "roc_auc": 0.9908, "accuracy": "97.7%", "precision": "65.0%", "recall": "89.0%", "f1": 0.751},
        {"rank": 6, "model": "ResNet-18", "roc_auc": 0.9848, "accuracy": "95.9%", "precision": "48.5%", "recall": "87.7%", "f1": 0.624},
    ],
    "ablation_results": [
        {"configuration": "FULL", "features": 33, "roc_auc": 1.0000, "accuracy": 1.0000, "precision": 1.0000, "recall": 1.0000, "f1": 1.0000, "time_s": 0.13},
        {"configuration": "NO_WATER_FRACTION", "features": 32, "roc_auc": 0.9998, "accuracy": 0.9867, "precision": 0.9822, "recall": 1.0000, "f1": 0.9910, "time_s": 0.05},
        {"configuration": "NO_NDWI", "features": 24, "roc_auc": 0.9899, "accuracy": 0.9469, "precision": 0.9639, "recall": 0.9639, "f1": 0.9639, "time_s": 0.10},
    ],
    "confusion_matrices": [
        {"model": "XGBoost", "test_patches": 1889, "missed_floods": 1, "false_positives": 11},
        {"model": "Random Forest", "test_patches": 1889, "missed_floods": 2, "false_positives": 15},
        {"model": "CNN", "test_patches": 1889, "missed_floods": 2, "false_positives": 13},
    ],
    "sensitivity_analysis": {
        "ndwi_threshold": "Optimal = 0.0; strong AUC above 0.99 from -0.2 to 0.2; degrades above 0.2.",
        "flood_fraction": "Optimal = 5%; AUC remained 1.0 across 1%-30%.",
        "patch_size": "32, 64, and 128 pixels tested; AUC remained 1.0 across all.",
    },
    "key_features": [
        {"rank": 1, "feature": "NDWI_p95", "description": "95th percentile of NDWI"},
        {"rank": 2, "feature": "Water fraction", "description": "Percentage of pixels with NDWI > 0.0"},
    ],
    "paper_notes": [
        "Study area: central Bangladesh using a 50 km buffer around Dhaka.",
        "Table A1 and Table 3 are treated as authoritative where prose conflicts with structured values.",
        "Open-Meteo forecasting is an operational extension, not a paper result.",
    ],
}
