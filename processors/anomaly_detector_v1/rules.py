from typing import Any

import pandas as pd

from processors.reconciliation_engine_v1 import normalise_employee_name

from .constants import MONEY_FIELDS, VARIANCE_RULES
from .utils import anomaly, display_employee, numeric, safe_reconciliation


def duplicate_employee_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for duplicate current-period employee names."""
    seen: dict[str, str] = {}
    duplicates: dict[str, str] = {}

    for row in current_rows or []:
        employee: str = display_employee(row.get("Employee"))
        key: str = normalise_employee_name(employee)

        if not key:
            continue

        if key in seen:
            duplicates[key] = seen[key]
        else:
            seen[key] = employee

    return [
        anomaly("HIGH", "Duplicate Employee", employee, "Employee", employee, "", "", f"Duplicate employee name found in current payroll: {employee}")
        for employee in duplicates.values()
    ]


def status_anomalies(reconciliation_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return anomalies for new and missing employees."""
    anomalies: list[dict[str, Any]] = []

    for _, row in safe_reconciliation(reconciliation_df).iterrows():
        status: str = str(row.get("Status", ""))

        if status == "Missing":
            employee: str = display_employee(row.get("Employee"))
            anomalies.append(anomaly("HIGH", "Missing Employee", employee, "Employee", "", employee, "", "Employee is missing from the current payroll."))

        if status == "New":
            employee = display_employee(row.get("Employee"))
            anomalies.append(anomaly("MEDIUM", "New Employee", employee, "Employee", employee, "", "", "Employee appears in the current payroll but not the previous payroll."))

    return anomalies


def variance_anomalies(reconciliation_df: pd.DataFrame, variance_threshold: float) -> list[dict[str, Any]]:
    """Return anomalies for employee-level field movements over threshold."""
    anomalies: list[dict[str, Any]] = []

    for _, row in safe_reconciliation(reconciliation_df).iterrows():
        if str(row.get("Status", "")) != "Existing":
            continue

        for field, severity in VARIANCE_RULES.items():
            anomalies.extend(field_variance_anomaly(row, field, severity, variance_threshold))

    return anomalies


def field_variance_anomaly(row: pd.Series, field: str, severity: str, variance_threshold: float) -> list[dict[str, Any]]:
    """Return a single variance anomaly when one field exceeds the threshold."""
    change_pct: float = numeric(row.get(f"{field} Change %"))

    if abs(change_pct) <= variance_threshold:
        return []

    employee: str = display_employee(row.get("Employee"))
    current_value: float = numeric(row.get(f"Current {field}"))
    previous_value: float = numeric(row.get(f"Previous {field}"))

    return [
        anomaly(
            severity,
            "Variance",
            employee,
            field,
            current_value,
            previous_value,
            change_pct,
            f"{field} changed by {change_pct:.2f}% for {employee}.",
        )
    ]


def zero_net_pay_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for current employees with zero net pay."""
    anomalies: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in current_rows or []:
        employee: str = display_employee(row.get("Employee"))
        employee_key: str = normalise_employee_name(employee)

        if numeric(row.get("NetPay")) == 0.0 and employee_key not in seen:
            seen.add(employee_key)
            anomalies.append(anomaly("HIGH", "Zero NetPay", employee, "NetPay", 0.0, "", "", f"Zero NetPay found for {employee}."))

    return anomalies


def negative_value_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for negative current-period money values."""
    anomalies: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for row in current_rows or []:
        employee: str = display_employee(row.get("Employee"))
        employee_key: str = normalise_employee_name(employee)

        for field in MONEY_FIELDS:
            value: float = numeric(row.get(field))
            issue_key: tuple[str, str] = (employee_key, field)

            if value < 0 and issue_key not in seen:
                seen.add(issue_key)
                anomalies.append(anomaly("HIGH", "Negative Value", employee, field, value, "", "", f"Negative {field} value found for {employee}."))

    return anomalies


def summary_anomalies(summary: dict, variance_threshold: float) -> list[dict[str, Any]]:
    """Return anomalies for total payroll movements over threshold."""
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
    """Return a total-level variance anomaly when a summary movement exceeds threshold."""
    change_pct: float = numeric(summary.get(change_pct_key))

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
