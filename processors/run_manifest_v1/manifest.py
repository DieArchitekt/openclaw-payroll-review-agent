import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from processors.path_display import display_path
from processors.payroll_review_workflow import PayrollReviewResult
from processors.versioning import (
    ACTIVE_AGENT_MODE,
    PAYROLL_RULE_VERSION,
    PAYROLL_SCHEMA_VERSION,
    RUN_MANIFEST_VERSION,
)


def build_run_manifest(
    result: PayrollReviewResult,
    *,
    current_path: Path,
    previous_path: Path,
    review_pack_path: Path,
    summary_json_path: Path | None,
    receipt_json_path: Path | None,
    manifest_json_path: Path | None,
    file_hashes: dict[str, str],
) -> dict[str, Any]:
    return {
        "manifest_version": RUN_MANIFEST_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "review_id": result.approval_record.review_id,
        "approval_status": result.approval_record.status,
        "prepared_by": result.approval_record.prepared_by,
        "schema_version": PAYROLL_SCHEMA_VERSION,
        "rule_version": PAYROLL_RULE_VERSION,
        "thresholds": result.thresholds,
        "file_hashes": file_hashes,
        "source_files": {
            "current_file": current_path.name,
            "previous_file": previous_path.name,
        },
        "generated_files": {
            "review_pack": display_path(review_pack_path),
            "summary_json": display_path(summary_json_path),
            "receipt_json": display_path(receipt_json_path),
            "manifest_json": display_path(manifest_json_path),
        },
        "anomaly_counts": {
            "high": (
                int((result.anomalies_df["Severity"] == "HIGH").sum())
                if not result.anomalies_df.empty
                else 0
            ),
            "medium": (
                int((result.anomalies_df["Severity"] == "MEDIUM").sum())
                if not result.anomalies_df.empty
                else 0
            ),
            "total": int(len(result.anomalies_df)),
        },
        "agent_mode": ACTIVE_AGENT_MODE,
        "human_action_required": True,
        "approval_performed_by_agent": False,
        "external_messages_sent": False,
        "source_files_modified": False,
    }


def manifest_json_bytes(manifest: dict[str, Any]) -> bytes:
    return json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
