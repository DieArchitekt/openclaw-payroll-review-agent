import pandas as pd
import streamlit as st


def render_table(label: str, df: pd.DataFrame) -> None:
    """Render a labelled dataframe or a small empty-state message."""
    st.subheader(label)

    if df.empty:
        st.info("No rows to show.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)
