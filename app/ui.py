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
from processors.payroll_review_workflow import PayrollReviewResult, run_payroll_review
from app.views.approval import render_approval
from app.views.anomalies import render_anomalies
from app.views.downloads import render_downloads
from app.views.fields import render_field_recognition
from app.views.summary import render_summary_cards
from app.views.tables import render_table
from gui.theme import use_streamlit_theme
from processors.payroll_processor_v1.workbook import exported_rows


def render_app() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    use_streamlit_theme(st)
    render_header()

    current_file, previous_file, variance_threshold = render_inputs()

    if st.button("Run payroll review", type="primary", use_container_width=True):
        if not current_file or not previous_file:
            st.error(
                "Upload both current and previous payroll files before running the review."
            )
            return

        with st.spinner(
            "Reading payroll files, reconciling payroll, and checking anomalies..."
        ):
            result: PayrollReviewResult = run_payroll_review(
                current_file, previous_file, variance_threshold
            )

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
        current_file = st.file_uploader(
            "Current payroll file", type=["pdf", "csv", "xlsx", "xlsm"]
        )
        previous_file = st.file_uploader(
            "Previous payroll file", type=["pdf", "csv", "xlsx", "xlsm"]
        )
        variance_threshold = st.slider(
            "Variance threshold %",
            min_value=MIN_VARIANCE_THRESHOLD,
            max_value=MAX_VARIANCE_THRESHOLD,
            value=DEFAULT_VARIANCE_THRESHOLD,
            step=1.0,
        )
        st.divider()
        st.caption(
            "The review compares employees by normalised name and flags material movements."
        )

    return current_file, previous_file, variance_threshold


def render_empty_state() -> None:
    st.info("Upload current and previous payroll files, then run the review.")


def render_review(result: PayrollReviewResult) -> None:
    render_summary_cards(result)

    tab_names = [
        "Approval",
        "Anomalies",
        "Reconciliation",
        "Current Payroll",
        "Previous Payroll",
        "Field Recognition",
        "Downloads",
    ]
    (
        approval_tab,
        anomalies_tab,
        reconciliation_tab,
        current_tab,
        previous_tab,
        fields_tab,
        downloads_tab,
    ) = st.tabs(tab_names)

    with approval_tab:
        render_approval(result)

    with anomalies_tab:
        render_anomalies(result.anomalies_df)

    with reconciliation_tab:
        render_table("Reconciliation", result.reconciliation_df)

    with current_tab:
        render_table(
            "Current Payroll",
            pd.DataFrame(exported_rows(result.current_extraction.rows)),
        )

    with previous_tab:
        render_table(
            "Previous Payroll",
            pd.DataFrame(exported_rows(result.previous_extraction.rows)),
        )

    with fields_tab:
        render_field_recognition(result)

    with downloads_tab:
        render_downloads(result)
