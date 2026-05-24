from difflib import SequenceMatcher
from typing import Any

from processors.reconciliation_engine_v1 import normalise_employee_name

from .utils import anomaly, display_employee, normalised_identifier, numeric, text_value


def duplicate_employee_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    seen: dict[str, str] = {}
    duplicates: dict[str, str] = {}

    for row in current_rows or []:
        employee = display_employee(row.get("Employee"))
        key = normalise_employee_name(employee)

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
    return duplicate_identifier_anomalies(
        current_rows,
        "BankAccount",
        "Duplicate Bank Account",
        "HIGH",
        "Bank account is used by more than one employee.",
    )


def duplicate_ni_number_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
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
