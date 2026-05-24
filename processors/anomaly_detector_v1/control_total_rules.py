from typing import Any

from .utils import anomaly, display_employee, numeric, text_value


def missing_department_cost_centre_anomalies(
    current_rows: list[dict],
) -> list[dict[str, Any]]:
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


def bacs_total_anomalies(
    current_rows: list[dict], summary: dict, tolerance: float
) -> list[dict[str, Any]]:
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
