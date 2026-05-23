import streamlit as st

from processors.approval_workflow_v1 import (
    approve_review,
    mark_exported,
    mark_reviewed,
    raise_queries,
    reject_review,
)
from processors.payroll_review_workflow import PayrollReviewResult
from processors.report_generator import generate_review_workbook


def render_approval(result: PayrollReviewResult) -> None:
    """Render approval status and workflow actions."""
    record = result.approval_record

    st.subheader("Approval")
    cols = st.columns(3)
    cols[0].metric("Status", record.status)
    cols[1].metric("Review ID", record.review_id)
    cols[2].metric("Prepared at", display_timestamp(record.prepared_at))

    user_name = st.text_input("Name", value=record.reviewed_by or record.approved_by)
    comments = st.text_area("Comments")

    action_cols = st.columns(5)

    if action_cols[0].button("Mark reviewed", use_container_width=True):
        run_approval_action(
            result,
            lambda: mark_reviewed(record, user_name, comments),
            "Review marked as reviewed.",
        )

    if action_cols[1].button("Raise queries", use_container_width=True):
        run_approval_action(
            result,
            lambda: raise_queries(record, user_name, comments),
            "Queries raised.",
        )

    if action_cols[2].button("Approve", use_container_width=True):
        run_approval_action(
            result,
            lambda: approve_review(record, user_name, comments),
            "Review approved.",
        )

    if action_cols[3].button("Reject", use_container_width=True):
        run_approval_action(
            result,
            lambda: reject_review(record, user_name, comments),
            "Review rejected.",
        )

    if action_cols[4].button("Mark exported", use_container_width=True):
        run_approval_action(
            result,
            lambda: mark_exported(record, user_name),
            "Review marked as exported for payment.",
        )


def run_approval_action(
    result: PayrollReviewResult, action, success_message: str
) -> None:
    """Run a transition, refresh workbook bytes, and show feedback."""
    try:
        action()
    except ValueError as exc:
        st.error(str(exc))
        return

    result.review_workbook_bytes = generate_review_workbook(result)
    st.session_state["review_result"] = result
    st.success(success_message)
    st.rerun()


def display_timestamp(value) -> str:
    """Return a readable timestamp for Streamlit metrics."""
    return value.strftime("%Y-%m-%d %H:%M") if value else ""
