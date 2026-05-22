from typing import Any

import pandas as pd

from .rules import (
    duplicate_employee_anomalies,
    negative_value_anomalies,
    status_anomalies,
    summary_anomalies,
    variance_anomalies,
    zero_net_pay_anomalies,
)
from .utils import anomalies_dataframe


def detect_anomalies(
    current_rows,
    reconciliation_df: pd.DataFrame,
    summary: dict,
    variance_threshold: float = 20.0,
) -> pd.DataFrame:
    """Return payroll review anomalies from current rows, reconciliation, and summary."""
    anomalies: list[dict[str, Any]] = []

    anomalies.extend(duplicate_employee_anomalies(current_rows))
    anomalies.extend(status_anomalies(reconciliation_df))
    anomalies.extend(variance_anomalies(reconciliation_df, variance_threshold))
    anomalies.extend(zero_net_pay_anomalies(current_rows))
    anomalies.extend(negative_value_anomalies(current_rows))
    anomalies.extend(summary_anomalies(summary, variance_threshold))

    return anomalies_dataframe(anomalies)
