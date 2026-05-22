from dataclasses import dataclass, field
from typing import Any, Protocol


class UploadedFile(Protocol):
    """Describe the uploaded file object used by Streamlit."""

    name: str

    def getvalue(self) -> bytes:
        """Return uploaded file contents as bytes."""


@dataclass(slots=True)
class RawPayrollSource:
    """Store raw tables and text lines read from one payroll source file."""

    tables: list[list[list[Any]]]
    raw_lines: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FieldMatch:
    """Store one source column to canonical payroll-field decision."""

    source_header: str
    canonical_field: str | None
    confidence: float
    status: str
    reason: str


@dataclass(slots=True)
class PayrollExtraction:
    """Collect extracted payroll rows plus field-recognition audit details."""

    rows: list[dict[str, Any]]
    field_matches: list[FieldMatch] = field(default_factory=list)
    unmapped_headers: list[str] = field(default_factory=list)
    raw_tables: list[list[list[str]]] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)
