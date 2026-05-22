import pandas as pd
import streamlit as st

from .tables import render_table


def render_anomalies(anomalies_df: pd.DataFrame) -> None:
    """Render anomaly rows with a severity filter."""
    if anomalies_df.empty:
        st.success("No anomalies found for the selected threshold.")
        return

    severity = st.radio("Severity", ["All", "HIGH", "MEDIUM"], horizontal=True)
    view = anomalies_df

    if severity != "All":
        view = anomalies_df[anomalies_df["Severity"] == severity]

    render_table("Anomalies", view)
