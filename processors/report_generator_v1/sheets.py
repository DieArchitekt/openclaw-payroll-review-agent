from typing import Any

import pandas as pd

from processors.payroll_processor_v1.recognition import field_match_rows
from processors.payroll_processor_v1.workbook import exported_rows

from .data import dataframe, summary_metrics


def write_report_sheets(
    writer: pd.ExcelWriter,
    current_extraction,
    previous_extraction,
    reconciliation_df,
    anomalies_df,
    summary,
) -> None:
    """Write all review output sheets."""
    write_dataframe(writer, "Current Payroll", exported_rows(current_extraction.rows))
    write_dataframe(writer, "Previous Payroll", exported_rows(previous_extraction.rows))
    write_dataframe(writer, "Reconciliation", reconciliation_df)
    write_dataframe(writer, "Anomalies", anomalies_df)
    write_summary_sheet(writer, summary, anomalies_df)
    write_dataframe(writer, "Current Field Recognition", field_match_rows(current_extraction.field_matches))
    write_dataframe(writer, "Previous Field Recognition", field_match_rows(previous_extraction.field_matches))


def write_dataframe(writer: pd.ExcelWriter, sheet_name: str, data: Any) -> None:
    """Write a DataFrame or list of dictionaries to a review output sheet."""
    dataframe(data).to_excel(writer, sheet_name=sheet_name, index=False)


def write_summary_sheet(writer: pd.ExcelWriter, summary: dict, anomalies_df: pd.DataFrame) -> None:
    """Write the review summary sheet."""
    pd.DataFrame(summary_metrics(summary, anomalies_df)).to_excel(writer, sheet_name="Summary", index=False, header=False)
