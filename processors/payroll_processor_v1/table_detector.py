from typing import Any

from .field_mapper import cell_is_numeric, infer_field, normalise_text


def clean_table(table: list[list[Any]]) -> list[list[str]]:
    """Return a rectangular table with stripped string cells."""
    width: int = max((len(row) for row in table), default=0)
    return [clean_row(row, width) for row in table]


def clean_row(row: list[Any], width: int) -> list[str]:
    """Return one table row as stripped strings padded to a common width."""
    return [("" if cell is None else str(cell).strip()) for cell in row] + [""] * (
        width - len(row)
    )


def find_header_row(table: list[list[str]]) -> int | None:
    """Return the index of the most likely header row in a table."""
    if not table:
        return None

    scored_rows: list[tuple[float, int]] = [
        (header_row_score(table[index], table[index + 1 : index + 6]), index)
        for index in range(min(8, len(table)))
    ]
    best_score, best_index = max(scored_rows, key=lambda item: item[0])

    return best_index if best_score >= 1.5 else None


def header_row_score(row: list[str], following_rows: list[list[str]]) -> float:
    """Return how likely a row is to contain payroll column headers."""
    alias_hits: int = sum(1 for cell in row if infer_field(cell, []).canonical_field)
    text_cells: int = sum(
        1 for cell in row if normalise_text(cell) and not cell_is_numeric(cell)
    )
    numeric_cells: int = sum(1 for cell in row if cell_is_numeric(cell))
    numeric_below: float = numeric_cells_below(following_rows)

    return (
        alias_hits * 2.0 + text_cells * 0.2 - numeric_cells * 0.5 + numeric_below * 0.1
    )


def numeric_cells_below(rows: list[list[str]]) -> float:
    """Return average numeric cells per following row."""
    if not rows:
        return 0.0

    return sum(sum(1 for cell in row if cell_is_numeric(cell)) for row in rows) / len(
        rows
    )
