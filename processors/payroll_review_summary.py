from pathlib import Path
from typing import Any

import pandas as pd

from processors.openclaw_reporting import ACTIVE_AGENT_MODE
from processors.payroll_review_workflow import PayrollReviewResult


def review_summary_payload(
    result: PayrollReviewResult,
    current_path: Path,
    previous_path: Path,
    output_path: Path,
    summary_json_path: Path | None = None,
    receipt_json_path: Path | None = None,
    manifest_json_path: Path | None = None,
    receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    counts = anomaly_counts(result.anomalies_df)
    receipt = receipt or {}

    return {
        "agent_mode": ACTIVE_AGENT_MODE,
        "review_id": result.approval_record.review_id,
        "approval_status": result.approval_record.status,
        "prepared_by": result.approval_record.prepared_by,
        "current_file": current_path.name,
        "previous_file": previous_path.name,
        "review_pack": str(output_path),
        "summary_json": str(summary_json_path) if summary_json_path else None,
        "agent_receipt_json": str(receipt_json_path) if receipt_json_path else None,
        "run_manifest_json": str(manifest_json_path) if manifest_json_path else None,
        "variance_threshold": result.variance_threshold,
        "summary": result.summary,
        "high_exception_count": counts["HIGH"],
        "medium_exception_count": counts["MEDIUM"],
        "exception_count": int(len(result.anomalies_df)),
        "run_status": receipt.get("run_status"),
        "recommended_next_action": receipt.get("recommended_next_action"),
        "ready_for_review": receipt.get("ready_for_review"),
        "ready_for_approval": receipt.get("ready_for_approval"),
        "blockers": receipt.get("blockers", []),
        "file_hashes": receipt.get("file_hashes", {}),
    }


def anomaly_counts(anomalies_df: pd.DataFrame) -> dict[str, int]:
    if anomalies_df.empty or "Severity" not in anomalies_df.columns:
        return {"HIGH": 0, "MEDIUM": 0}

    counts = anomalies_df["Severity"].value_counts()
    return {"HIGH": int(counts.get("HIGH", 0)), "MEDIUM": int(counts.get("MEDIUM", 0))}
