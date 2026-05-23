import pandas as pd
import streamlit as st

from processors.payroll_review_workflow import PayrollReviewResult
from processors.payroll_processor_v1.recognition import field_match_rows
from .tables import render_table


def render_field_recognition(result: PayrollReviewResult) -> None:
    """Render current and previous field-recognition results."""
    left, right = st.columns(2)

    with left:
        render_table(
            "Current field recognition",
            pd.DataFrame(field_match_rows(result.current_extraction.field_matches)),
        )

    with right:
        render_table(
            "Previous field recognition",
            pd.DataFrame(field_match_rows(result.previous_extraction.field_matches)),
        )
