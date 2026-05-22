import re
from typing import Any

from .field_mapper import NUMBER_PATTERN, parse_number
from .models import FieldMatch, PayrollExtraction
from .row_normaliser import row_has_payroll_data
from .schema import POSITIONAL_FALLBACK_FIELDS, field_is_exported


SPACED_ROW_PATTERN: re.Pattern[str] = re.compile(r"^(\d+)?\s*([A-Za-z][A-Za-z\s,'\-.]+?)\s+(.+)$")


def extract_lines_as_fallback(raw_lines: list[str]) -> list[dict[str, Any]]:
    """Return payroll rows parsed from text lines when table extraction is weak."""
    return [row for row in (fallback_extract_line(line) for line in raw_lines) if row]


def fallback_extract_line(line: str) -> dict[str, Any] | None:
    """Return a generic row from a dense payroll line when no table is available."""
    values: list[str] = NUMBER_PATTERN.findall(line)

    if len(values) < 6:
        return None

    row: dict[str, Any] = fallback_person_fields(line, values[0])
    row.update(fallback_money_fields(values))

    return row if row_has_payroll_data(row) else None


def fallback_person_fields(line: str, first_value: str) -> dict[str, Any]:
    """Return employee reference/name fields inferred from a dense text line."""
    match: re.Match[str] | None = SPACED_ROW_PATTERN.match(line)

    if match:
        reference, possible_name, _ = match.groups()
        row: dict[str, Any] = {"Employee": possible_name.strip()}

        if reference:
            row["EmployeeRef"] = reference

        return row

    text_before_values: str = line.split(first_value, 1)[0].strip()
    return {"Employee": text_before_values} if text_before_values else {}


def fallback_money_fields(values: list[str]) -> dict[str, Any]:
    """Return money fields inferred by generic fallback position."""
    return {
        field_name: parse_number(values[index])
        for index, field_name in enumerate(POSITIONAL_FALLBACK_FIELDS)
        if index < len(values)
    }


def add_fallback_matches(extraction: PayrollExtraction) -> None:
    """Add low-confidence field-recognition records for fallback extraction."""
    for field_name in POSITIONAL_FALLBACK_FIELDS:
        extraction.field_matches.append(
            FieldMatch(
                source_header=f"positional fallback: {field_name}",
                canonical_field=field_name,
                confidence=0.5,
                status="exported" if field_is_exported(field_name) else "recognised_ignored",
                reason="fallback position from dense payroll row",
            )
        )
