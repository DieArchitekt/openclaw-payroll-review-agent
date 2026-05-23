from .constants import (
    STATUS_APPROVED,
    STATUS_EXPORTED,
    STATUS_PREPARED,
    STATUS_QUERIES_RAISED,
    STATUS_REJECTED,
    STATUS_REVIEWED,
)
from .models import ApprovalRecord, current_timestamp

ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
    STATUS_PREPARED: (STATUS_REVIEWED, STATUS_QUERIES_RAISED),
    STATUS_QUERIES_RAISED: (STATUS_REVIEWED,),
    STATUS_REVIEWED: (STATUS_APPROVED, STATUS_REJECTED),
    STATUS_APPROVED: (STATUS_EXPORTED,),
    STATUS_REJECTED: (),
    STATUS_EXPORTED: (),
}


def create_approval_record(prepared_by: str = "") -> ApprovalRecord:
    """Return a new approval record at Prepared status."""
    return ApprovalRecord(prepared_by=prepared_by)


def mark_reviewed(
    record: ApprovalRecord, reviewer_name: str, comments: str = ""
) -> ApprovalRecord:
    """Move a record to Reviewed and store reviewer details."""
    move_status(record, STATUS_REVIEWED)
    record.reviewed_by = reviewer_name
    record.reviewed_at = current_timestamp()
    record.reviewer_comments = comments
    touch(record)
    return record


def raise_queries(
    record: ApprovalRecord, reviewer_name: str, query_notes: str = ""
) -> ApprovalRecord:
    """Move a record to Queries raised and store query details."""
    move_status(record, STATUS_QUERIES_RAISED)
    record.reviewed_by = reviewer_name
    record.reviewed_at = current_timestamp()
    record.query_notes = query_notes
    touch(record)
    return record


def approve_review(
    record: ApprovalRecord, approver_name: str, comments: str = ""
) -> ApprovalRecord:
    """Move a reviewed record to Approved and store approver details."""
    move_status(record, STATUS_APPROVED)
    record.approved_by = approver_name
    record.approved_at = current_timestamp()
    record.approval_comments = comments
    touch(record)
    return record


def reject_review(
    record: ApprovalRecord, approver_name: str, reason: str = ""
) -> ApprovalRecord:
    """Move a reviewed record to Rejected and store rejection details."""
    move_status(record, STATUS_REJECTED)
    record.approved_by = approver_name
    record.approved_at = current_timestamp()
    record.rejection_reason = reason
    touch(record)
    return record


def mark_exported(record: ApprovalRecord, user_name: str) -> ApprovalRecord:
    """Move an approved record to Exported for payment."""
    move_status(record, STATUS_EXPORTED)
    record.exported_by = user_name
    record.exported_at = current_timestamp()
    touch(record)
    return record


def move_status(record: ApprovalRecord, next_status: str) -> None:
    """Move the record status when the transition is allowed."""
    allowed_statuses: tuple[str, ...] = ALLOWED_TRANSITIONS.get(record.status, ())

    if next_status not in allowed_statuses:
        raise ValueError(
            f"Cannot move approval status from {record.status} to {next_status}."
        )

    record.status = next_status


def touch(record: ApprovalRecord) -> None:
    """Update the record modified timestamp."""
    record.last_updated_at = current_timestamp()
