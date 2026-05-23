from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from processors.anomaly_detector_v1 import detect_anomalies
from processors.approval_workflow_v1 import ApprovalRecord, create_approval_record
from processors.payroll_processor_v1.extractor import extract_payroll
from processors.payroll_processor_v1.io_utils import write_uploaded_file
from processors.payroll_processor_v1.models import PayrollExtraction, UploadedFile
from processors.reconciliation_engine_v1 import reconcile_payroll
from processors.report_generator import generate_review_workbook


@dataclass(slots=True)
class PayrollReviewResult:
    current_extraction: PayrollExtraction
    previous_extraction: PayrollExtraction
    reconciliation_df: pd.DataFrame
    anomalies_df: pd.DataFrame
    summary: dict[str, Any]
    variance_threshold: float
    approval_record: ApprovalRecord
    review_workbook_bytes: bytes = b""


def run_payroll_review(
    current_file: UploadedFile,
    previous_file: UploadedFile,
    variance_threshold: float,
    prepared_by: str = "",
) -> PayrollReviewResult:
    """Run extraction, reconciliation, anomaly detection, and report generation."""
    current_path: Path = write_uploaded_file(current_file)
    previous_path: Path = write_uploaded_file(previous_file)

    try:
        current_extraction: PayrollExtraction = extract_payroll(current_path)
        previous_extraction: PayrollExtraction = extract_payroll(previous_path)
    finally:
        current_path.unlink(missing_ok=True)
        previous_path.unlink(missing_ok=True)

    reconciliation_df, summary = reconcile_payroll(
        current_extraction.rows, previous_extraction.rows
    )
    anomalies_df: pd.DataFrame = detect_anomalies(
        current_extraction.rows,
        reconciliation_df,
        summary,
        variance_threshold=variance_threshold,
    )
    approval_record: ApprovalRecord = create_approval_record(prepared_by=prepared_by)
    result = PayrollReviewResult(
        current_extraction=current_extraction,
        previous_extraction=previous_extraction,
        reconciliation_df=reconciliation_df,
        anomalies_df=anomalies_df,
        summary=summary,
        variance_threshold=variance_threshold,
        approval_record=approval_record,
    )
    result.review_workbook_bytes = generate_review_workbook(result)

    return result


def severity_counts(anomalies_df: pd.DataFrame) -> dict[str, int]:
    """Return anomaly counts used by the dashboard summary."""
    if anomalies_df.empty or "Severity" not in anomalies_df.columns:
        return {"HIGH": 0, "MEDIUM": 0}

    counts = anomalies_df["Severity"].value_counts()
    return {
        "HIGH": int(counts.get("HIGH", 0)),
        "MEDIUM": int(counts.get("MEDIUM", 0)),
    }
