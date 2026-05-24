from typing import Any

import pandas as pd

from .constants import VARIANCE_RULES
from .utils import anomaly, display_employee, numeric, safe_reconciliation


def variance_anomalies(
    reconciliation_df: pd.DataFrame, variance_threshold: float
) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []

    for _, row in safe_reconciliation(reconciliation_df).iterrows():
        if str(row.get("Status", "")) != "Existing":
            continue

        for field, severity in VARIANCE_RULES.items():
            anomalies.extend(
                field_variance_anomaly(row, field, severity, variance_threshold)
            )

    return anomalies


def field_variance_anomaly(
    row: pd.Series, field: str, severity: str, variance_threshold: float
) -> list[dict[str, Any]]:
    change_pct = numeric(row.get(f"{field} Change %"))

    if abs(change_pct) <= variance_threshold:
        return []

    employee = display_employee(row.get("Employee"))
    current_value = numeric(row.get(f"Current {field}"))
    previous_value = numeric(row.get(f"Previous {field}"))
    category = (
        "Variable Pay Movement"
        if field in {"Bonus", "Overtime", "Commission"}
        else "Variance"
    )

    return [
        anomaly(
            severity,
            category,
            employee,
            field,
            current_value,
            previous_value,
            change_pct,
            f"{field} changed by {change_pct:.2f}% for {employee}.",
        )
    ]


def summary_anomalies(summary: dict, variance_threshold: float) -> list[dict[str, Any]]:
    return summary_variance_anomaly(
        summary,
        "NetPay",
        "current_total_net_pay",
        "previous_total_net_pay",
        "net_pay_change_pct",
        variance_threshold,
    ) + summary_variance_anomaly(
        summary,
        "EmployerCost",
        "current_total_employer_cost",
        "previous_total_employer_cost",
        "employer_cost_change_pct",
        variance_threshold,
    )


def summary_variance_anomaly(
    summary: dict,
    field: str,
    current_key: str,
    previous_key: str,
    change_pct_key: str,
    variance_threshold: float,
) -> list[dict[str, Any]]:
    change_pct = numeric(summary.get(change_pct_key))

    if abs(change_pct) <= variance_threshold:
        return []

    return [
        anomaly(
            "MEDIUM",
            "Total Movement",
            "",
            field,
            numeric(summary.get(current_key)),
            numeric(summary.get(previous_key)),
            change_pct,
            f"Total {field} changed by {change_pct:.2f}%.",
        )
    ]
