from typing import Any

PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "developer message",
    "reveal hidden",
    "send this file",
    "email this file",
    "delete the source",
    "approve payroll automatically",
    "mark payroll approved",
)


def contains_prompt_injection_text(value: Any) -> bool:
    text = str(value or "").lower()
    return any(marker in text for marker in PROMPT_INJECTION_MARKERS)


def prompt_injection_fields(row: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in row.items()
        if isinstance(value, str) and contains_prompt_injection_text(value)
    ]
