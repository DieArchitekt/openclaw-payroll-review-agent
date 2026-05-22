from pathlib import Path
from typing import Any

from .field_mapper import unique_field_matches
from .fallback_parser import add_fallback_matches, extract_lines_as_fallback
from .models import FieldMatch, PayrollExtraction, RawPayrollSource
from .row_normaliser import normalise_table_rows
from .source_reader import read_payroll_source
from .table_detector import clean_table, find_header_row


def extract_payroll(source_path: Path) -> PayrollExtraction:
    """Return payroll rows from a source file using dynamic table recognition."""
    source: RawPayrollSource = read_payroll_source(source_path)
    extraction: PayrollExtraction = extract_tables(source)

    if extraction.rows:
        return extraction

    extraction.rows = extract_lines_as_fallback(extraction.raw_lines)
    add_fallback_matches(extraction)

    return extraction


def extract_tables(source: RawPayrollSource) -> PayrollExtraction:
    """Return payroll data extracted from recognised source tables."""
    extraction: PayrollExtraction = PayrollExtraction(rows=[], raw_lines=source.raw_lines)

    for table in source.tables:
        append_table_rows(extraction, clean_table(table))

    extraction.unmapped_headers = unmapped_headers(extraction.field_matches)

    return extraction


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


def unmapped_headers(matches: list[FieldMatch]) -> list[str]:
    """Return sorted source headers that were not mapped to a canonical field."""
    return sorted({match.source_header for match in matches if match.status == "unmapped" and match.source_header})
