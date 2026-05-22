from typing import Any

import pandas as pd


def dataframe(data: Any) -> pd.DataFrame:
    """Return data as a pandas DataFrame."""
    if isinstance(data, pd.DataFrame):
        return data

    return pd.DataFrame(data or [])


def anomaly_counts(anomalies_df: pd.DataFrame) -> dict[str, int]:
    """Return anomaly counts by severity."""
    if anomalies_df is None or anomalies_df.empty or "Severity" not in anomalies_df.columns:
        return {"HIGH": 0, "MEDIUM": 0}

    counts = anomalies_df["Severity"].value_counts()
    return {"HIGH": int(counts.get("HIGH", 0)), "MEDIUM": int(counts.get("MEDIUM", 0))}


def summary_metrics(summary: dict, anomalies_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return summary rows with visual section breaks."""
    counts: dict[str, int] = anomaly_counts(anomalies_df)

    return [
        {"Metric": "Employee counts", "Value": ""},
        {"Metric": "current employee count", "Value": summary.get("current_employee_count", 0)},
        {"Metric": "previous employee count", "Value": summary.get("previous_employee_count", 0)},
        {"Metric": "new employee count", "Value": summary.get("new_employee_count", 0)},
        {"Metric": "missing employee count", "Value": summary.get("missing_employee_count", 0)},
        {"Metric": "Payroll totals", "Value": ""},
        {"Metric": "current total net pay", "Value": summary.get("current_total_net_pay", 0.0)},
        {"Metric": "previous total net pay", "Value": summary.get("previous_total_net_pay", 0.0)},
        {"Metric": "net pay change", "Value": summary.get("net_pay_change", 0.0)},
        {"Metric": "employer cost change", "Value": summary.get("employer_cost_change", 0.0)},
        {"Metric": "employer cost change %", "Value": summary.get("employer_cost_change_pct", 0.0)},
        {"Metric": "Anomalies", "Value": ""},
        {"Metric": "HIGH anomalies", "Value": counts["HIGH"]},
        {"Metric": "MEDIUM anomalies", "Value": counts["MEDIUM"]},
    ]
