import pandas as pd
import streamlit as st

from .tables import render_table


def render_anomalies(anomalies_df: pd.DataFrame) -> None:
    """Render anomaly rows with a severity filter."""
    if anomalies_df.empty:
        st.success("No anomalies found for the selected threshold.")
        return

    filter_cols = st.columns([1, 2, 2])
    severities = ["All", *sorted(anomalies_df["Severity"].dropna().unique())]
    categories = ["All", *sorted(anomalies_df["Category"].dropna().unique())]
    severity = filter_cols[0].selectbox("Severity", severities)
    category = filter_cols[1].selectbox("Category", categories)
    employee_search = filter_cols[2].text_input("Employee search")
    view = anomalies_df

    if severity != "All":
        view = anomalies_df[anomalies_df["Severity"] == severity]

    if category != "All":
        view = view[view["Category"] == category]

    if employee_search:
        view = view[
            view["Employee"]
            .astype(str)
            .str.contains(employee_search, case=False, na=False)
        ]

    st.caption(f"{len(view)} of {len(anomalies_df)} exceptions shown.")
    render_table("Exceptions", sorted_anomalies(view))


def sorted_anomalies(anomalies_df: pd.DataFrame) -> pd.DataFrame:
    """Return anomalies sorted by finance review priority."""
    severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return (
        anomalies_df.assign(
            _severity_rank=anomalies_df["Severity"].map(severity_rank).fillna(9)
        )
        .sort_values(["_severity_rank", "Category", "Employee"])
        .drop(columns=["_severity_rank"])
    )
