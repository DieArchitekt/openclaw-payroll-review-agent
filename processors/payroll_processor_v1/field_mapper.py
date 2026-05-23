import re
from difflib import SequenceMatcher
from typing import Any, Iterable

from .models import FieldMatch
from .schema import (
    HEADER_CONFIDENCE_THRESHOLD,
    PAYROLL_SCHEMA,
    field_is_exported,
    field_kind,
)

NUMBER_PATTERN: re.Pattern[str] = re.compile(r"-?\(?\u00a3?\d[\d,]*\.?\d*\)?")


def normalise_text(value: Any) -> str:
    """Return lowercase alphanumeric text used for fuzzy field matching."""
    text: str = "" if value is None else str(value)
    text = text.replace("&", " and ")
    text = re.sub(r"[/_:\-]+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9 ]+", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def parse_number(value: Any) -> float | str:
    """Return a float for money-like values and original text otherwise."""
    text: str = "" if value is None else str(value).strip()

    if not text:
        return 0.0

    negative: bool = text.startswith("(") and text.endswith(")")
    cleaned: str = strip_currency(text)

    try:
        amount: float = float(cleaned)
    except ValueError:
        return text

    return -amount if negative else amount


def strip_currency(text: str) -> str:
    """Return numeric-looking text without currency or wrapper characters."""
    return (
        text.replace("\u00a3", "")
        .replace("\u00c2\u00a3", "")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
    )


def cell_is_numeric(value: Any) -> bool:
    """Return whether a cell looks like a numeric payroll value."""
    return bool(value is not None and NUMBER_PATTERN.fullmatch(str(value).strip()))


def numeric_density(values: list[Any]) -> float:
    """Return the share of non-empty sample cells that look numeric."""
    populated: list[Any] = [value for value in values if str(value or "").strip()]

    if not populated:
        return 0.0

    return sum(1 for value in populated if cell_is_numeric(value)) / len(populated)


def match_score(candidate: str, aliases: Iterable[str]) -> tuple[float, str]:
    """Return the best fuzzy score and reason for a candidate header."""
    normalised_candidate: str = normalise_text(candidate)
    best_score: float = 0.0
    best_alias: str = ""

    for alias in aliases:
        score: float = score_alias(normalised_candidate, normalise_text(alias))

        if score > best_score:
            best_score = score
            best_alias = alias

    reason: str = f"closest alias: {best_alias}" if best_alias else "no close alias"
    return best_score, reason


def score_alias(candidate: str, alias: str) -> float:
    """Return a similarity score between normalised header text and one alias."""
    if not candidate or not alias:
        return 0.0

    if candidate == alias:
        return 1.0

    if alias in candidate or candidate in alias:
        return min(0.95, 0.75 + len(alias) / max(len(candidate), 1) * 0.2)

    return SequenceMatcher(None, candidate, alias).ratio()


def infer_field(header: str, sample_values: list[Any]) -> FieldMatch:
    """Return the most likely canonical payroll field for a source header."""
    best_field: str | None = None
    best_score: float = 0.0
    best_reason: str = "no close alias"

    for field_name, field_info in PAYROLL_SCHEMA.items():
        score, reason = match_score(header, field_info["aliases"])

        if score > best_score:
            best_field = field_name
            best_score = score
            best_reason = reason

    best_score, best_reason = boost_numeric_match(
        best_field, best_score, best_reason, sample_values
    )

    if best_field and best_score >= HEADER_CONFIDENCE_THRESHOLD:
        status: str = (
            "exported" if field_is_exported(best_field) else "recognised_ignored"
        )
        return FieldMatch(header, best_field, round(best_score, 3), status, best_reason)

    return FieldMatch(header, None, round(best_score, 3), "unmapped", best_reason)


def boost_numeric_match(
    field_name: str | None,
    score: float,
    reason: str,
    sample_values: list[Any],
) -> tuple[float, str]:
    """Return a slightly stronger score when a money field has numeric samples."""
    if (
        field_name
        and field_kind(field_name) in {"money", "number"}
        and numeric_density(sample_values) > 0.8
    ):
        return min(1.0, score + 0.05), f"{reason}; numeric column"

    return score, reason


def unique_field_matches(headers: list[str], rows: list[list[str]]) -> list[FieldMatch]:
    """Return one best mapping decision for every source header."""
    matches: list[FieldMatch] = []
    claimed_fields: dict[str, FieldMatch] = {}

    for col_idx, header in enumerate(headers):
        candidate: FieldMatch = infer_field(header, column_sample(rows, col_idx))
        resolve_duplicate_mapping(candidate, claimed_fields, header)
        matches.append(candidate)

    return matches


def column_sample(rows: list[list[str]], col_idx: int) -> list[str]:
    """Return sample values from one source column."""
    return [row[col_idx] for row in rows[:20] if col_idx < len(row)]


def resolve_duplicate_mapping(
    candidate: FieldMatch,
    claimed_fields: dict[str, FieldMatch],
    header: str,
) -> None:
    """Mutate mapping decisions so only one source column owns a canonical field."""
    if not candidate.canonical_field:
        return

    previous: FieldMatch | None = claimed_fields.get(candidate.canonical_field)

    if not previous or candidate.confidence > previous.confidence:
        replace_previous_mapping(previous, header)
        claimed_fields[candidate.canonical_field] = candidate
        return

    candidate.status = "unmapped"
    candidate.reason = f"duplicate mapping kept as {previous.source_header}"


def replace_previous_mapping(previous: FieldMatch | None, header: str) -> None:
    """Mark a replaced duplicate field mapping as unmapped."""
    if not previous:
        return

    previous.status = "unmapped"
    previous.reason = f"duplicate mapping replaced by {header}"
