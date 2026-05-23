import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SCHEMA_PATH: Path = Path(__file__).with_name("payroll_schema.json")


@lru_cache(maxsize=1)
def payroll_schema_data() -> dict[str, Any]:
    """Return payroll schema settings from the package data file."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


PAYROLL_SCHEMA: dict[str, dict[str, Any]] = payroll_schema_data()["fields"]
EXPORT_FIELDS: list[str] = payroll_schema_data()["export_fields"]
POSITIONAL_FALLBACK_FIELDS: list[str] = payroll_schema_data()[
    "positional_fallback_fields"
]
HEADER_CONFIDENCE_THRESHOLD: float = float(
    payroll_schema_data()["header_confidence_threshold"]
)


def field_kind(field_name: str) -> str:
    """Return the value type for a canonical field."""
    return PAYROLL_SCHEMA[field_name]["kind"]


def field_is_exported(field_name: str) -> bool:
    """Return whether a canonical field should appear in the main export."""
    return bool(PAYROLL_SCHEMA[field_name]["export"])


def output_header(field_name: str) -> str:
    """Return the export label for a canonical field."""
    return PAYROLL_SCHEMA[field_name]["label"]
