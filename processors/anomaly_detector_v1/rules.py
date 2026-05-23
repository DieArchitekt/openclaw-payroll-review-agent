from difflib import SequenceMatcher
from typing import Any

import pandas as pd

from processors.reconciliation_engine_v1 import normalise_employee_name

from .constants import MONEY_FIELDS, VARIANCE_RULES
from .utils import (
    anomaly,
    display_employee,
    is_truthy,
    normalised_identifier,
    numeric,
    safe_reconciliation,
    text_value,
)


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
        anomaly(
            "HIGH",
            "Duplicate Employee",
            employee,
            "Employee",
            employee,
            "",
            "",
            f"Duplicate employee name found in current payroll: {employee}",
        )
        for employee in duplicates.values()
    ]


def duplicate_bank_account_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for bank accounts used by more than one employee."""
    return duplicate_identifier_anomalies(
        current_rows,
        "BankAccount",
        "Duplicate Bank Account",
        "HIGH",
        "Bank account is used by more than one employee.",
    )


def duplicate_ni_number_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for NI numbers used by more than one employee."""
    return duplicate_identifier_anomalies(
        current_rows,
        "NationalInsuranceNumber",
        "Duplicate NI Number",
        "HIGH",
        "National Insurance number is used by more than one employee.",
    )


def duplicate_identifier_anomalies(
    current_rows: list[dict],
    field: str,
    category: str,
    severity: str,
    message: str,
) -> list[dict[str, Any]]:
    """Return duplicate identifier anomalies for one field."""
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str]] = []

    for row in current_rows or []:
        identifier = normalised_identifier(row.get(field))
        employee = display_employee(row.get("Employee"))

        if not identifier:
            continue

        if identifier in seen and seen[identifier] != employee:
            duplicates.append((employee, text_value(row.get(field))))
        else:
            seen[identifier] = employee

    return [
        anomaly(
            severity,
            category,
            employee,
            field,
            value,
            "",
            "",
            f"{message} Employee: {employee}.",
        )
        for employee, value in duplicates
    ]


def similar_name_duplicate_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for employees with highly similar names and pay values."""
    anomalies: list[dict[str, Any]] = []
    rows = [
        row
        for row in current_rows or []
        if display_employee(row.get("Employee")) and numeric(row.get("NetPay")) > 0
    ]

    for left_index, left_row in enumerate(rows):
        left_name = display_employee(left_row.get("Employee"))
        left_key = normalise_employee_name(left_name)

        for right_row in rows[left_index + 1 :]:
            right_name = display_employee(right_row.get("Employee"))
            right_key = normalise_employee_name(right_name)

            if not left_key or left_key == right_key:
                continue

            score = SequenceMatcher(None, left_key, right_key).ratio()
            if score >= 0.88:
                anomalies.append(
                    anomaly(
                        "MEDIUM",
                        "Possible Duplicate Employee",
                        left_name,
                        "Employee",
                        left_name,
                        right_name,
                        round(score * 100, 2),
                        f"Possible duplicate employee names: {left_name} and {right_name}.",
                    )
                )

    return anomalies


def status_anomalies(reconciliation_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return anomalies for new and missing employees."""
    anomalies: list[dict[str, Any]] = []

    for _, row in safe_reconciliation(reconciliation_df).iterrows():
        status: str = str(row.get("Status", ""))

        if status == "Missing":
            employee: str = display_employee(row.get("Employee"))
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


def variance_anomalies(
    reconciliation_df: pd.DataFrame, variance_threshold: float
) -> list[dict[str, Any]]:
    """Return anomalies for employee-level field movements over threshold."""
    anomalies: list[dict[str, Any]] = []

    for _, row in safe_reconciliation(reconciliation_df).iterrows():
        if str(row.get("Status", "")) != "Existing":
            continue

        for field, severity in VARIANCE_RULES.items():
            anomalies.extend(
                field_variance_anomaly(row, field, severity, variance_threshold)
            )

    return anomalies


def leaver_still_paid_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for leavers who still have current-period pay."""
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
    """Return anomalies for starters without an approval marker."""
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


def high_net_pay_anomalies(
    current_rows: list[dict], threshold: float
) -> list[dict[str, Any]]:
    """Return anomalies for employees above the high net pay threshold."""
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        net_pay = numeric(row.get("NetPay"))
        if net_pay > threshold:
            employee = display_employee(row.get("Employee"))
            anomalies.append(
                anomaly(
                    "MEDIUM",
                    "High NetPay",
                    employee,
                    "NetPay",
                    net_pay,
                    threshold,
                    "",
                    f"NetPay exceeds threshold for {employee}.",
                )
            )

    return anomalies


def gross_pay_zero_tax_ni_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for gross pay with no PAYE or employee NI."""
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        gross_pay = numeric(row.get("GrossPay"))
        if (
            gross_pay > 0
            and numeric(row.get("PAYE")) == 0
            and numeric(row.get("EmployeeNI")) == 0
        ):
            employee = display_employee(row.get("Employee"))
            anomalies.append(
                anomaly(
                    "HIGH",
                    "Gross Pay With No Tax or NI",
                    employee,
                    "PAYE/EmployeeNI",
                    gross_pay,
                    "",
                    "",
                    f"GrossPay exists but PAYE and EmployeeNI are zero for {employee}.",
                )
            )

    return anomalies


def missing_pension_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for missing pension deductions or employer pension values."""
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        gross_pay = numeric(row.get("GrossPay"))
        if gross_pay <= 0:
            continue

        employee = display_employee(row.get("Employee"))
        if numeric(row.get("EmployerPension")) == 0:
            anomalies.append(
                anomaly(
                    "MEDIUM",
                    "Employer Pension Missing",
                    employee,
                    "EmployerPension",
                    0.0,
                    "",
                    "",
                    f"Employer pension is missing for {employee}.",
                )
            )

        if (
            numeric(row.get("PreTaxPension")) == 0
            and numeric(row.get("PostTaxPension")) == 0
        ):
            anomalies.append(
                anomaly(
                    "MEDIUM",
                    "Employee Pension Missing",
                    employee,
                    "PreTaxPension/PostTaxPension",
                    0.0,
                    "",
                    "",
                    f"Employee pension deduction is missing for {employee}.",
                )
            )

    return anomalies


def low_tax_ratio_anomalies(
    current_rows: list[dict],
    low_paye_ratio: float,
    low_ni_ratio: float,
) -> list[dict[str, Any]]:
    """Return anomalies for PAYE or NI that look low against gross pay."""
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        gross_pay = numeric(row.get("GrossPay"))
        if gross_pay <= 0:
            continue

        employee = display_employee(row.get("Employee"))
        paye_ratio = numeric(row.get("PAYE")) / gross_pay
        ni_ratio = numeric(row.get("EmployeeNI")) / gross_pay

        if paye_ratio < low_paye_ratio:
            anomalies.append(
                anomaly(
                    "MEDIUM",
                    "Low PAYE Ratio",
                    employee,
                    "PAYE",
                    numeric(row.get("PAYE")),
                    gross_pay,
                    round(paye_ratio * 100, 2),
                    f"PAYE looks low against GrossPay for {employee}.",
                )
            )

        if ni_ratio < low_ni_ratio:
            anomalies.append(
                anomaly(
                    "MEDIUM",
                    "Low NI Ratio",
                    employee,
                    "EmployeeNI",
                    numeric(row.get("EmployeeNI")),
                    gross_pay,
                    round(ni_ratio * 100, 2),
                    f"EmployeeNI looks low against GrossPay for {employee}.",
                )
            )

    return anomalies


def missing_department_cost_centre_anomalies(
    current_rows: list[dict],
) -> list[dict[str, Any]]:
    """Return anomalies for missing department or cost centre values."""
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        employee = display_employee(row.get("Employee"))

        for field, category in (
            ("Department", "Missing Department"),
            ("CostCentre", "Missing CostCentre"),
        ):
            if not text_value(row.get(field)):
                anomalies.append(
                    anomaly(
                        "MEDIUM",
                        category,
                        employee,
                        field,
                        "",
                        "",
                        "",
                        f"{field} is missing for {employee}.",
                    )
                )

    return anomalies


def negative_net_pay_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for negative current-period net pay."""
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        net_pay = numeric(row.get("NetPay"))
        if net_pay < 0:
            employee = display_employee(row.get("Employee"))
            anomalies.append(
                anomaly(
                    "HIGH",
                    "Negative NetPay",
                    employee,
                    "NetPay",
                    net_pay,
                    "",
                    "",
                    f"Negative NetPay found for {employee}.",
                )
            )

    return anomalies


def bacs_total_anomalies(
    current_rows: list[dict], summary: dict, tolerance: float
) -> list[dict[str, Any]]:
    """Return anomalies when BACS amount total does not agree to NetPay."""
    bacs_values = [
        numeric(row.get("BACSAmount"))
        for row in current_rows or []
        if row.get("BACSAmount") not in (None, "")
    ]

    if not bacs_values:
        return []

    bacs_total = sum(bacs_values)
    net_pay_total = numeric(summary.get("current_total_net_pay"))
    difference = bacs_total - net_pay_total

    if abs(difference) <= tolerance:
        return []

    return [
        anomaly(
            "HIGH",
            "BACS Control Difference",
            "",
            "BACSAmount",
            bacs_total,
            net_pay_total,
            "",
            f"BACS total differs from current NetPay total by {difference:.2f}.",
        )
    ]


def field_variance_anomaly(
    row: pd.Series, field: str, severity: str, variance_threshold: float
) -> list[dict[str, Any]]:
    """Return a single variance anomaly when one field exceeds the threshold."""
    change_pct: float = numeric(row.get(f"{field} Change %"))

    if abs(change_pct) <= variance_threshold:
        return []

    employee: str = display_employee(row.get("Employee"))
    current_value: float = numeric(row.get(f"Current {field}"))
    previous_value: float = numeric(row.get(f"Previous {field}"))

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


def zero_net_pay_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    """Return anomalies for current employees with zero net pay."""
    anomalies: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in current_rows or []:
        employee: str = display_employee(row.get("Employee"))
        employee_key: str = normalise_employee_name(employee)

        if numeric(row.get("NetPay")) == 0.0 and employee_key not in seen:
            seen.add(employee_key)
            anomalies.append(
                anomaly(
                    "HIGH",
                    "Zero NetPay",
                    employee,
                    "NetPay",
                    0.0,
                    "",
                    "",
                    f"Zero NetPay found for {employee}.",
                )
            )

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
                anomalies.append(
                    anomaly(
                        "HIGH",
                        "Negative Value",
                        employee,
                        field,
                        value,
                        "",
                        "",
                        f"Negative {field} value found for {employee}.",
                    )
                )

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
