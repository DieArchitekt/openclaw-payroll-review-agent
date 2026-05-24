from typing import Any

from processors.reconciliation_engine_v1 import normalise_employee_name

from .constants import MONEY_FIELDS
from .utils import anomaly, display_employee, numeric


def high_net_pay_anomalies(
    current_rows: list[dict], threshold: float
) -> list[dict[str, Any]]:
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


def negative_net_pay_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
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


def zero_net_pay_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in current_rows or []:
        employee = display_employee(row.get("Employee"))
        employee_key = normalise_employee_name(employee)

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
    anomalies: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for row in current_rows or []:
        employee = display_employee(row.get("Employee"))
        employee_key = normalise_employee_name(employee)

        for field in MONEY_FIELDS:
            value = numeric(row.get(field))
            issue_key = (employee_key, field)

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
