from typing import Any

from .models import FieldMatch


def field_match_rows(matches: list[FieldMatch]) -> list[dict[str, Any]]:
    """Return table-friendly field-recognition rows."""
    return [
        {
            "Source header": match.source_header,
            "Canonical field": match.canonical_field or "",
            "Status": match.status,
            "Confidence": match.confidence,
            "Reason": match.reason,
        }
        for match in matches
    ]
