from typing import Any

import pandas as pd

from .constants import ANOMALY_COLUMNS


def anomalies_dataframe(anomalies: list[dict[str, Any]]) -> pd.DataFrame:
    """Return anomalies as a DataFrame with a stable column order."""
    return pd.DataFrame(anomalies, columns=ANOMALY_COLUMNS)


def anomaly(
    severity: str,
    category: str,
    employee: Any,
    field: str,
    current_value: Any,
    previous_value: Any,
    change_pct: Any,
    message: str,
) -> dict[str, Any]:
    """Return one anomaly row."""
    return {
        "Severity": severity,
        "Category": category,
        "Employee": display_employee(employee),
        "Field": field,
        "Current Value": current_value,
        "Previous Value": previous_value,
        "Change %": change_pct,
        "Message": message,
    }


def display_employee(value: Any) -> str:
    """Return a clean employee display value."""
    if value is None or pd.isna(value):
        return ""

    return str(value).strip()


def numeric(value: Any) -> float:
    """Return a numeric value for anomaly checks."""
    value = pd.to_numeric(value, errors="coerce")

    if pd.isna(value):
        return 0.0

    return float(value)


def safe_reconciliation(reconciliation_df: pd.DataFrame) -> pd.DataFrame:
    """Return a reconciliation DataFrame with expected basics available."""
    if reconciliation_df is None or reconciliation_df.empty:
        return pd.DataFrame(columns=["Employee", "Status"])

    return reconciliation_df
