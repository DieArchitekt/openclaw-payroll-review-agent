import re
from pathlib import Path
from typing import Any

import pdfplumber

from .field_mapper import NUMBER_PATTERN, cell_is_numeric, infer_field, normalise_text, parse_number
from .field_mapper import unique_field_matches
from .models import FieldMatch, PayrollExtraction
from .schema import PAYROLL_SCHEMA, POSITIONAL_FALLBACK_FIELDS, field_is_exported, field_kind


SPACED_ROW_PATTERN: re.Pattern[str] = re.compile(r"^(\d+)?\s*([A-Za-z][A-Za-z\s,'\-.]+?)\s+(.+)$")


def extract_payroll(pdf_path: Path) -> PayrollExtraction:
    """Return payroll rows from a PDF using dynamic tables first and text fallback second."""
    extraction: PayrollExtraction = extract_tables_from_pdf(pdf_path)

    if extraction.rows:
        return extraction

    extraction.rows = extract_lines_as_fallback(pdf_path, extraction.raw_lines)
    add_fallback_matches(extraction)

    return extraction


def extract_tables_from_pdf(pdf_path: Path) -> PayrollExtraction:
    """Return payroll data extracted from recognised PDF tables."""
    extraction: PayrollExtraction = PayrollExtraction(rows=[])

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            collect_page_lines(extraction, page.extract_text())
            collect_page_tables(extraction, page.extract_tables() or [])

    extraction.unmapped_headers = unmapped_headers(extraction.field_matches)

    return extraction


def collect_page_lines(extraction: PayrollExtraction, page_text: str | None) -> None:
    """Append non-empty page text lines to the raw extraction audit trail."""
    if page_text:
        extraction.raw_lines.extend(line for line in page_text.splitlines() if line.strip())


def collect_page_tables(extraction: PayrollExtraction, tables: list[list[list[Any]]]) -> None:
    """Append recognised rows from all PDF tables on a page."""
    for table in tables:
        append_table_rows(extraction, clean_table(table))


def append_table_rows(extraction: PayrollExtraction, table: list[list[str]]) -> None:
    """Append recognised rows from one cleaned table."""
    extraction.raw_tables.append(table)
    header_index: int | None = find_header_row(table)

    if header_index is None:
        return

    headers: list[str] = table[header_index]
    data_rows: list[list[str]] = table[header_index + 1:]
    matches: list[FieldMatch] = unique_field_matches(headers, data_rows)

    extraction.field_matches.extend(matches)
    extraction.rows.extend(normalise_table_rows(headers, data_rows, matches))


def clean_table(table: list[list[Any]]) -> list[list[str]]:
    """Return a rectangular table with stripped string cells."""
    width: int = max((len(row) for row in table), default=0)
    return [clean_row(row, width) for row in table]


def clean_row(row: list[Any], width: int) -> list[str]:
    """Return one table row as stripped strings padded to a common width."""
    return [("" if cell is None else str(cell).strip()) for cell in row] + [""] * (width - len(row))


def find_header_row(table: list[list[str]]) -> int | None:
    """Return the index of the most likely header row in a table."""
    if not table:
        return None

    scored_rows: list[tuple[float, int]] = [
        (header_row_score(table[index], table[index + 1:index + 6]), index)
        for index in range(min(8, len(table)))
    ]
    best_score, best_index = max(scored_rows, key=lambda item: item[0])

    return best_index if best_score >= 1.5 else None


def header_row_score(row: list[str], following_rows: list[list[str]]) -> float:
    """Return how likely a row is to contain payroll column headers."""
    alias_hits: int = sum(1 for cell in row if infer_field(cell, []).canonical_field)
    text_cells: int = sum(1 for cell in row if normalise_text(cell) and not cell_is_numeric(cell))
    numeric_cells: int = sum(1 for cell in row if cell_is_numeric(cell))
    numeric_below: float = numeric_cells_below(following_rows)

    return alias_hits * 2.0 + text_cells * 0.2 - numeric_cells * 0.5 + numeric_below * 0.1


def numeric_cells_below(rows: list[list[str]]) -> float:
    """Return average numeric cells per following row."""
    if not rows:
        return 0.0

    return sum(sum(1 for cell in row if cell_is_numeric(cell)) for row in rows) / len(rows)


def normalise_table_rows(headers: list[str], rows: list[list[str]], matches: list[FieldMatch]) -> list[dict[str, Any]]:
    """Return canonical payroll dictionaries from mapped table rows."""
    return [row for row in (normalise_table_row(headers, source_row, matches) for source_row in rows) if row_has_payroll_data(row)]


def normalise_table_row(headers: list[str], source_row: list[str], matches: list[FieldMatch]) -> dict[str, Any]:
    """Return one canonical payroll dictionary from one source table row."""
    row: dict[str, Any] = {}
    unknown_index: int = 1

    for col_idx, value in enumerate(source_row):
        unknown_index = add_source_value(row, headers, matches, col_idx, value, unknown_index)

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
        header: str = headers[col_idx] if col_idx < len(headers) else f"Column {col_idx + 1}"
        row[f"Unmapped_{unknown_index}_{header}"] = value
        return unknown_index + 1

    return unknown_index


def coerce_field_value(field_name: str, value: Any) -> Any:
    """Return a value coerced according to the canonical payroll field type."""
    return parse_number(value) if field_kind(field_name) in {"money", "number"} else value


def row_has_payroll_data(row: dict[str, Any]) -> bool:
    """Return whether a normalised row looks like payroll data."""
    has_person: bool = bool(row.get("Employee") or row.get("EmployeeRef"))
    has_money: bool = any(isinstance(value, (int, float)) and value != 0 for value in row.values())

    return bool(row and (has_person or has_money))


def unmapped_headers(matches: list[FieldMatch]) -> list[str]:
    """Return sorted source headers that were not mapped to a canonical field."""
    return sorted({match.source_header for match in matches if match.status == "unmapped" and match.source_header})


def extract_lines_as_fallback(pdf_path: Path, raw_lines: list[str]) -> list[dict[str, Any]]:
    """Return payroll rows parsed from text lines when table extraction is weak."""
    return [row for row in (fallback_extract_line(line) for line in lines_for_fallback(pdf_path, raw_lines)) if row]


def lines_for_fallback(pdf_path: Path, raw_lines: list[str]) -> list[str]:
    """Return existing raw lines or lazily extract lines from the PDF."""
    if raw_lines:
        return raw_lines

    lines: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text: str | None = page.extract_text()
            if text:
                lines.extend(line for line in text.splitlines() if line.strip())

    return lines


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
