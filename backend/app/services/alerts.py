def alert_message(country: str, risk_level: str, probability: float) -> str:
    """Create a concise operational alert message."""

    return f"{country}: {risk_level} flood risk detected at {probability:.1%} likelihood."
