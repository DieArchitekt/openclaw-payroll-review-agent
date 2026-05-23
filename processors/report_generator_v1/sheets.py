from typing import Any

import pandas as pd

from processors.payroll_processor_v1.recognition import field_match_rows
from processors.payroll_processor_v1.workbook import exported_rows

from .data import approval_rows, approval_summary_metrics, dataframe, summary_metrics


def write_report_sheets(
    writer: pd.ExcelWriter,
    current_extraction,
    previous_extraction,
    reconciliation_df,
    anomalies_df,
    summary,
    approval_record=None,
) -> None:
    """Write all review output sheets."""
    write_dataframe(writer, "Current Payroll", exported_rows(current_extraction.rows))
    write_dataframe(writer, "Previous Payroll", exported_rows(previous_extraction.rows))
    write_dataframe(writer, "Reconciliation", reconciliation_df)
    write_dataframe(writer, "Anomalies", anomalies_df)
    write_summary_sheet(writer, summary, anomalies_df, approval_record)
    write_approval_sheet(writer, approval_record)
    write_dataframe(
        writer,
        "Current Field Recognition",
        field_match_rows(current_extraction.field_matches),
    )
    write_dataframe(
        writer,
        "Previous Field Recognition",
        field_match_rows(previous_extraction.field_matches),
    )


def write_dataframe(writer: pd.ExcelWriter, sheet_name: str, data: Any) -> None:
    """Write a DataFrame or list of dictionaries to a review output sheet."""
    dataframe(data).to_excel(writer, sheet_name=sheet_name, index=False)


def write_summary_sheet(
    writer: pd.ExcelWriter,
    summary: dict,
    anomalies_df: pd.DataFrame,
    approval_record=None,
) -> None:
    """Write the review summary sheet."""
    rows = approval_summary_metrics(approval_record) + summary_metrics(
        summary, anomalies_df
    )
    pd.DataFrame(rows).to_excel(writer, sheet_name="Summary", index=False, header=False)


def write_approval_sheet(writer: pd.ExcelWriter, approval_record) -> None:
    """Write approval audit details."""
    write_dataframe(writer, "Approval", approval_rows(approval_record))
