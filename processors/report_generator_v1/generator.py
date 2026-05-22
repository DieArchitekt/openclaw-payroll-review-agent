from io import BytesIO
from pathlib import Path

import pandas as pd

from .sheets import write_report_sheets
from .styles import format_standard_sheet, style_anomaly_sheet, write_summary_metrics


def generate_review_workbook(
    result,
    output_path=None,
) -> bytes | str:
    """Generate a payroll review agent output file."""
    buffer: BytesIO = BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        write_report_sheets(
            writer,
            result.current_extraction,
            result.previous_extraction,
            result.reconciliation_df,
            result.anomalies_df,
            result.summary,
        )
        format_workbook(writer.book)

    workbook_bytes: bytes = buffer.getvalue()

    if output_path:
        path = Path(output_path)
        path.write_bytes(workbook_bytes)
        return str(path)

    return workbook_bytes


def format_workbook(workbook) -> None:
    """Apply formatting to every review output sheet."""
    for worksheet in workbook.worksheets:
        format_standard_sheet(worksheet)

    style_anomaly_sheet(workbook["Anomalies"])
    write_summary_metrics(workbook["Summary"])
