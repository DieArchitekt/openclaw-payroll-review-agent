from processors.agent_controls_v1.confirmations import (
    HumanConfirmation,
    validate_human_confirmation,
)
from processors.approval_workflow_v1 import (
    ApprovalRecord,
    mark_reviewed,
    raise_queries,
)


def agent_can_create_prepared_by_running_review() -> bool:
    return True


def agent_suggest_reviewed(record: ApprovalRecord, comment: str = "") -> dict[str, str]:
    return {
        "review_id": record.review_id,
        "current_status": record.status,
        "suggested_status": "Reviewed",
        "comment": comment,
    }


def agent_mark_reviewed_with_confirmation(
    record: ApprovalRecord,
    reviewer_name: str,
    comments: str,
    confirmation: HumanConfirmation | None,
) -> ApprovalRecord:
    validate_human_confirmation(
        confirmation,
        action="mark_reviewed",
        review_id=record.review_id,
    )
    return mark_reviewed(record, reviewer_name, comments)


def agent_raise_queries_with_confirmation(
    record: ApprovalRecord,
    reviewer_name: str,
    query_notes: str,
    confirmation: HumanConfirmation | None,
) -> ApprovalRecord:
    validate_human_confirmation(
        confirmation,
        action="raise_queries",
        review_id=record.review_id,
    )
    return raise_queries(record, reviewer_name, query_notes)


def block_agent_approval() -> None:
    raise PermissionError("Agent may not approve, reject, or export payroll.")
