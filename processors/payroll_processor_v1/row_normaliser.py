from typing import Any

from .field_mapper import parse_number
from .models import FieldMatch
from .schema import PAYROLL_SCHEMA, field_kind


def normalise_table_rows(
    headers: list[str], rows: list[list[str]], matches: list[FieldMatch]
) -> list[dict[str, Any]]:
    """Return canonical payroll dictionaries from mapped table rows."""
    return [
        row
        for row in (
            normalise_table_row(headers, source_row, matches) for source_row in rows
        )
        if row_has_payroll_data(row)
    ]


def normalise_table_row(
    headers: list[str], source_row: list[str], matches: list[FieldMatch]
) -> dict[str, Any]:
    """Return one canonical payroll dictionary from one source table row."""
    row: dict[str, Any] = {}
    unknown_index: int = 1

    for col_idx, value in enumerate(source_row):
        unknown_index = add_source_value(
            row, headers, matches, col_idx, value, unknown_index
        )

    return row


def add_source_value(
    row: dict[str, Any],
    headers: list[str],
    matches: list[FieldMatch],
    col_idx: int,
    value: str,
    unknown_index: int,
) -> int:
    """Add one source value to a canonical row or an unmapped field."""
    match: FieldMatch | None = matches[col_idx] if col_idx < len(matches) else None

    if match and match.canonical_field:
        row[match.canonical_field] = coerce_field_value(match.canonical_field, value)
        return unknown_index

    if str(value).strip():
        header: str = (
            headers[col_idx] if col_idx < len(headers) else f"Column {col_idx + 1}"
        )
        row[f"Unmapped_{unknown_index}_{header}"] = value
        return unknown_index + 1

    return unknown_index


def coerce_field_value(field_name: str, value: Any) -> Any:
    """Return a value coerced according to the canonical payroll field type."""
    return (
        parse_number(value) if field_kind(field_name) in {"money", "number"} else value
    )


def row_has_payroll_data(row: dict[str, Any]) -> bool:
    """Return whether a normalised row looks like payroll data."""
    has_person: bool = bool(row.get("Employee") or row.get("EmployeeRef"))
    has_money: bool = any(
        isinstance(value, (int, float)) and value != 0 for value in row.values()
    )

    return bool(row and (has_person or has_money))


def exported_default(field_name: str) -> Any:
    """Return a default value for one canonical export field."""
    return 0.0 if PAYROLL_SCHEMA[field_name]["kind"] in {"money", "number"} else ""
