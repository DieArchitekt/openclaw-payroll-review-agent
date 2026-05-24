import pandas as pd
import streamlit as st

from processors.agent_controls_v1.constants import ACTIVE_AGENT_MODE
from processors.payroll_review_workflow import PayrollReviewResult

from .tables import render_table


def render_agent_activity(result: PayrollReviewResult) -> None:
    st.subheader("Agent Activity")
    cols = st.columns(4)
    cols[0].metric("Agent mode", ACTIVE_AGENT_MODE)
    cols[1].metric("Review ID", result.approval_record.review_id)
    cols[2].metric("Approval status", result.approval_record.status)
    cols[3].metric("Human required", "Yes")

    activity = getattr(result, "agent_activity", []) or []

    if not activity:
        st.info("No agent activity has been recorded for this review session.")
        return

    render_table("Activity", pd.DataFrame(activity))

    manifest = getattr(result, "manifest", {}) or {}

    if manifest:
        with st.expander("Run manifest preview"):
            st.json(manifest)
