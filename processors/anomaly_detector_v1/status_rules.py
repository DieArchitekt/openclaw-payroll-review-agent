from typing import Any

import pandas as pd

from .utils import (
    anomaly,
    display_employee,
    is_truthy,
    numeric,
    safe_reconciliation,
    text_value,
)


def status_anomalies(reconciliation_df: pd.DataFrame) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []

    for _, row in safe_reconciliation(reconciliation_df).iterrows():
        status = str(row.get("Status", ""))

        if status == "Missing":
            employee = display_employee(row.get("Employee"))
            anomalies.append(
                anomaly(
                    "HIGH",
                    "Missing Employee",
                    employee,
                    "Employee",
                    "",
                    employee,
                    "",
                    "Employee is missing from the current payroll.",
                )
            )

        if status == "New":
            employee = display_employee(row.get("Employee"))
            anomalies.append(
                anomaly(
                    "MEDIUM",
                    "New Employee",
                    employee,
                    "Employee",
                    employee,
                    "",
                    "",
                    "Employee appears in the current payroll but not the previous payroll.",
                )
            )

    return anomalies


def leaver_still_paid_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        employee = display_employee(row.get("Employee"))
        is_leaver = is_truthy(row.get("LeaverFlag")) or bool(
            text_value(row.get("LeaveDate"))
        )
        paid_value = max(numeric(row.get("NetPay")), numeric(row.get("GrossPay")))

        if is_leaver and paid_value > 0:
            anomalies.append(
                anomaly(
                    "HIGH",
                    "Leaver Still Paid",
                    employee,
                    "LeaverFlag",
                    paid_value,
                    "",
                    "",
                    f"Leaver still has payroll value for {employee}.",
                )
            )

    return anomalies


def starter_without_approval_anomalies(
    current_rows: list[dict],
) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        employee = display_employee(row.get("Employee"))
        is_starter = is_truthy(row.get("StarterFlag")) or bool(
            text_value(row.get("StartDate"))
        )

        if is_starter and not is_truthy(row.get("StarterApproval")):
            anomalies.append(
                anomaly(
                    "HIGH",
                    "Starter Approval Missing",
                    employee,
                    "StarterApproval",
                    text_value(row.get("StarterApproval")),
                    "",
                    "",
                    f"Starter approval is missing for {employee}.",
                )
            )

    return anomalies
