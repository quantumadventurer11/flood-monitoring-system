def risk_level(probability: float) -> str:
    """Map flood probability to the shared Low/Medium/High thresholds."""

    if probability < 0.30:
        return "Low"
    if probability <= 0.60:
        return "Medium"
    return "High"


def classification(probability: float) -> str:
    return "flood" if probability >= 0.5 else "no_flood"
