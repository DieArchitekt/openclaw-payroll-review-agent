from typing import Any

from processors.privacy_v1.prompt_injection import prompt_injection_fields

from .utils import anomaly, display_employee


def prompt_injection_anomalies(current_rows: list[dict]) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []

    for row in current_rows or []:
        employee = display_employee(row.get("Employee"))

        for field in prompt_injection_fields(row):
            anomalies.append(
                anomaly(
                    "HIGH",
                    "Prompt Injection Text",
                    employee,
                    field,
                    "[redacted instruction-like text]",
                    "",
                    "",
                    (
                        f"Instruction-like text was found in {field} for "
                        f"{employee or 'an employee'}."
                    ),
                )
            )

    return anomalies
