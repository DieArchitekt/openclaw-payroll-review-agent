import re
from typing import Any

import pandas as pd


def normalise_employee_name(name: str) -> str:
    """Return a stable employee key for matching payroll rows across periods."""
    text: str = "" if name is None else str(name)
    text = text.strip().lower()

    if "," in text:
        parts: list[str] = [part.strip() for part in text.split(",", maxsplit=1)]
        text = " ".join(reversed(parts))

    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def display_employee_name(row: pd.Series) -> str:
    """Return the best available display name for a reconciled employee."""
    current_name: str = clean_display_name(row.get("Employee_current"))
    previous_name: str = clean_display_name(row.get("Employee_previous"))

    return current_name or previous_name


def clean_display_name(value: Any) -> str:
    """Return a display name without pandas missing-value artefacts."""
    if pd.isna(value):
        return ""

    return str(value).strip()
