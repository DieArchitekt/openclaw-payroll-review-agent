from typing import Any


def money(value: Any) -> str:
    """Return a display string for GBP values."""
    try:
        return f"GBP {float(value):,.2f}"
    except (TypeError, ValueError):
        return "GBP 0.00"
