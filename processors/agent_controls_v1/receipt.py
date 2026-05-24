from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from processors.agent_controls_v1.constants import (
    ACTIVE_AGENT_MODE,
    RECOMMEND_HIGH_ANOMALIES,
)
from processors.agent_controls_v1.review_gate import review_gate
from processors.payroll_review_workflow import PayrollReviewResult
from processors.versioning import PAYROLL_RULE_VERSION, PAYROLL_SCHEMA_VERSION

RUN_STATUS_BLOCKED = "blocked"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_COMPLETED_WITH_EXCEPTIONS = "completed_with_exceptions"


def build_agent_receipt(
    result: PayrollReviewResult,
    review_pack_path: Path,
    summary_json_path: Path | None,
    *,
    current_file_hash: str = "",
    previous_file_hash: str = "",
    workbook_hash: str = "",
    summary_json_hash: str = "",
) -> dict[str, Any]:
    gate = review_gate(result)
    high_count = int(gate["high_anomaly_count"])
    medium_count = int(gate["medium_anomaly_count"])

    return {
        "agent_mode": ACTIVE_AGENT_MODE,
        "review_id": result.approval_record.review_id,
        "approval_status": result.approval_record.status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "human_action_required": True,
        "recommended_next_action": recommended_next_action(gate, high_count),
        "source_files_modified": False,
        "external_messages_sent": False,
        "approval_performed_by_agent": False,
        "run_status": run_status(result, high_count, medium_count),
        "review_pack": str(review_pack_path),
        "summary_json": str(summary_json_path) if summary_json_path else None,
        "file_hashes": {
            "current_file_sha256": current_file_hash,
            "previous_file_sha256": previous_file_hash,
            "review_workbook_sha256": workbook_hash,
            "summary_json_sha256": summary_json_hash,
        },
        "run_metadata": {
            "variance_threshold": getattr(result, "variance_threshold", None),
            "thresholds": getattr(result, "thresholds", {}),
            "schema_version": PAYROLL_SCHEMA_VERSION,
            "rule_version": PAYROLL_RULE_VERSION,
        },
        "high_anomaly_count": high_count,
        "medium_anomaly_count": medium_count,
        "total_anomaly_count": int(len(result.anomalies_df)),
        "ready_for_review": bool(gate["ready_for_review"]),
        "ready_for_approval": False,
        "blockers": gate["blockers"],
        "critical_controls": {
            "required_fields_mapped": required_fields_mapped(result),
            "review_pack_generated": bool(result.review_workbook_bytes),
            "high_anomalies_present": bool(high_count),
            "prompt_injection_text_present": prompt_injection_present(result),
        },
    }


def run_status(
    result: PayrollReviewResult,
    high_count: int,
    medium_count: int,
) -> str:
    if not result.current_extraction.rows or not result.previous_extraction.rows:
        return RUN_STATUS_BLOCKED

    if high_count or medium_count:
        return RUN_STATUS_COMPLETED_WITH_EXCEPTIONS

    return RUN_STATUS_COMPLETED


def recommended_next_action(gate: dict[str, object], high_count: int) -> str:
    if high_count:
        return RECOMMEND_HIGH_ANOMALIES

    return str(gate["recommended_next_action"])


def required_fields_mapped(result: PayrollReviewResult) -> bool:
    return bool(result.current_extraction.rows) and bool(
        result.previous_extraction.rows
    )


def prompt_injection_present(result: PayrollReviewResult) -> bool:
    anomalies_df = result.anomalies_df

    if anomalies_df.empty or "Category" not in anomalies_df.columns:
        return False

    return bool((anomalies_df["Category"] == "Prompt Injection Text").any())
