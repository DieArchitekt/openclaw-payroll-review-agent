from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from .constants import STATUS_PREPARED


def new_review_id() -> str:
    """Return a unique review id for one payroll approval record."""
    return str(uuid4())


def current_timestamp() -> datetime:
    """Return a timezone-aware timestamp for approval audit fields."""
    return datetime.now(UTC)


@dataclass(slots=True)
class ApprovalRecord:
    """Store the approval state and sign-off details for one payroll review."""

    review_id: str = field(default_factory=new_review_id)
    status: str = STATUS_PREPARED
    prepared_by: str = ""
    prepared_at: datetime = field(default_factory=current_timestamp)
    reviewed_by: str = ""
    reviewed_at: datetime | None = None
    approved_by: str = ""
    approved_at: datetime | None = None
    exported_by: str = ""
    exported_at: datetime | None = None
    reviewer_comments: str = ""
    approval_comments: str = ""
    query_notes: str = ""
    rejection_reason: str = ""
    last_updated_at: datetime = field(default_factory=current_timestamp)
