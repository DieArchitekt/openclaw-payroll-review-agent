from typing import Any

import streamlit as st

from processors.payroll_review_workflow import PayrollReviewResult, severity_counts
from .formatting import money


def render_summary_cards(result: PayrollReviewResult) -> None:
    """Render the headline payroll review metrics."""
    counts: dict[str, int] = severity_counts(result.anomalies_df)
    summary: dict[str, Any] = result.summary
    cols = st.columns(6)

    cols[0].metric("Current employees", summary.get("current_employee_count", 0))
    cols[1].metric("Previous employees", summary.get("previous_employee_count", 0))
    cols[2].metric("New", summary.get("new_employee_count", 0))
    cols[3].metric("Missing", summary.get("missing_employee_count", 0))
    cols[4].metric("High anomalies", counts["HIGH"])
    cols[5].metric("Medium anomalies", counts["MEDIUM"])

    cost_cols = st.columns(4)
    cost_cols[0].metric(
        "Current NetPay", money(summary.get("current_total_net_pay", 0.0))
    )
    cost_cols[1].metric(
        "NetPay change",
        money(summary.get("net_pay_change", 0.0)),
        f"{summary.get('net_pay_change_pct', 0.0):.2f}%",
    )
    cost_cols[2].metric(
        "Current employer cost", money(summary.get("current_total_employer_cost", 0.0))
    )
    cost_cols[3].metric(
        "Employer cost change",
        money(summary.get("employer_cost_change", 0.0)),
        f"{summary.get('employer_cost_change_pct', 0.0):.2f}%",
    )
