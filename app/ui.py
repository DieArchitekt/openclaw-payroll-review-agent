from typing import Any

import pandas as pd
import streamlit as st

from app.config import (
    APP_CAPTION,
    APP_TITLE,
    DEFAULT_VARIANCE_THRESHOLD,
    MAX_VARIANCE_THRESHOLD,
    MIN_VARIANCE_THRESHOLD,
)
from app.payroll_review_workflow import PayrollReviewResult, build_review_workbook, run_payroll_review, severity_counts
from gui.theme import use_streamlit_theme
from processors.payroll_processor_v1.streamlit_app import field_match_rows
from processors.payroll_processor_v1.workbook import exported_rows


def render_app() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    use_streamlit_theme(st)
    render_header()

    current_file, previous_file, variance_threshold = render_inputs()

    if st.button("Run payroll review", type="primary", use_container_width=True):
        if not current_file or not previous_file:
            st.error("Upload both current and previous payroll files before running the review.")
            return

        with st.spinner("Reading payroll files, reconciling payroll, and checking anomalies..."):
            result: PayrollReviewResult = run_payroll_review(current_file, previous_file, variance_threshold)

        st.session_state["review_result"] = result

    result = st.session_state.get("review_result")

    if result:
        render_review(result)
    else:
        render_empty_state()


def render_header() -> None:
    st.title(APP_TITLE)
    st.caption(APP_CAPTION)


def render_inputs() -> tuple[Any, Any, float]:
    with st.sidebar:
        st.header("Review setup")
        current_file = st.file_uploader("Current payroll file", type=["pdf"])
        previous_file = st.file_uploader("Previous payroll file", type=["pdf"])
        variance_threshold = st.slider(
            "Variance threshold %",
            min_value=MIN_VARIANCE_THRESHOLD,
            max_value=MAX_VARIANCE_THRESHOLD,
            value=DEFAULT_VARIANCE_THRESHOLD,
            step=1.0,
        )
        st.divider()
        st.caption("The review compares employees by normalised name and flags material movements.")

    return current_file, previous_file, variance_threshold


def render_empty_state() -> None:
    st.info("Upload current and previous payroll files, then run the review.")


def render_review(result: PayrollReviewResult) -> None:
    render_summary_cards(result)

    tab_names = ["Anomalies", "Reconciliation", "Current Payroll", "Previous Payroll", "Field Recognition", "Downloads"]
    anomalies_tab, reconciliation_tab, current_tab, previous_tab, fields_tab, downloads_tab = st.tabs(tab_names)

    with anomalies_tab:
        render_anomalies(result.anomalies_df)

    with reconciliation_tab:
        render_table("Reconciliation", result.reconciliation_df)

    with current_tab:
        render_table("Current Payroll", pd.DataFrame(exported_rows(result.current_extraction.rows)))

    with previous_tab:
        render_table("Previous Payroll", pd.DataFrame(exported_rows(result.previous_extraction.rows)))

    with fields_tab:
        render_field_recognition(result)

    with downloads_tab:
        render_downloads(result)


def render_summary_cards(result: PayrollReviewResult) -> None:
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
    cost_cols[0].metric("Current NetPay", money(summary.get("current_total_net_pay", 0.0)))
    cost_cols[1].metric("NetPay change", money(summary.get("net_pay_change", 0.0)), f"{summary.get('net_pay_change_pct', 0.0):.2f}%")
    cost_cols[2].metric("Current employer cost", money(summary.get("current_total_employer_cost", 0.0)))
    cost_cols[3].metric(
        "Employer cost change",
        money(summary.get("employer_cost_change", 0.0)),
        f"{summary.get('employer_cost_change_pct', 0.0):.2f}%",
    )


def render_anomalies(anomalies_df: pd.DataFrame) -> None:
    if anomalies_df.empty:
        st.success("No anomalies found for the selected threshold.")
        return

    severity = st.radio("Severity", ["All", "HIGH", "MEDIUM"], horizontal=True)
    view = anomalies_df

    if severity != "All":
        view = anomalies_df[anomalies_df["Severity"] == severity]

    render_table("Anomalies", view)


def render_table(label: str, df: pd.DataFrame) -> None:
    st.subheader(label)

    if df.empty:
        st.info("No rows to show.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_field_recognition(result: PayrollReviewResult) -> None:
    left, right = st.columns(2)

    with left:
        render_table("Current field recognition", pd.DataFrame(field_match_rows(result.current_extraction.field_matches)))

    with right:
        render_table("Previous field recognition", pd.DataFrame(field_match_rows(result.previous_extraction.field_matches)))


def render_downloads(result: PayrollReviewResult) -> None:
    st.subheader("Downloads")
    st.download_button(
        "Download full review pack",
        data=build_review_workbook(result),
        file_name="payroll_review.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.download_button(
        "Download anomalies CSV",
        data=result.anomalies_df.to_csv(index=False).encode("utf-8"),
        file_name="payroll_anomalies.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.download_button(
        "Download reconciliation CSV",
        data=result.reconciliation_df.to_csv(index=False).encode("utf-8"),
        file_name="payroll_reconciliation.csv",
        mime="text/csv",
        use_container_width=True,
    )


def money(value: Any) -> str:
    try:
        return f"GBP {float(value):,.2f}"
    except (TypeError, ValueError):
        return "GBP 0.00"
