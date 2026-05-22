import streamlit as st

from processors.payroll_review_workflow import PayrollReviewResult


def render_downloads(result: PayrollReviewResult) -> None:
    """Render payroll review download buttons."""
    st.subheader("Downloads")
    st.download_button(
        "Download full review pack",
        data=result.review_workbook_bytes,
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
