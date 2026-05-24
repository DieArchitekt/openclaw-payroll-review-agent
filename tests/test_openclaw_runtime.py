import json
from pathlib import Path

from processors.openclaw_runtime_v1 import (
    load_runtime_policy,
    validate_review_outputs,
    validate_runtime_environment,
)


def test_runtime_policy_loads_expected_read_only_contract():
    policy = load_runtime_policy()

    assert policy["agent_mode"] == "read_only_review"
    assert "scripts/run_openclaw_payroll_review.ps1" in policy["allowed_commands"]
    assert "outputs/reviews" in policy["allowed_write_roots"]
    assert policy["required_receipt_flags"]["human_action_required"] is True


def test_runtime_environment_validation_passes_for_repo():
    result = validate_runtime_environment(Path.cwd())

    assert result.ok is True
    assert result.errors == []


def test_review_output_validation_accepts_safe_receipt_and_manifest(tmp_path):
    prefix = "sample"
    receipt = {
        "agent_mode": "read_only_review",
        "human_action_required": True,
        "source_files_modified": False,
        "external_messages_sent": False,
        "approval_performed_by_agent": False,
        "review_id": "REV-1",
        "review_pack": str(tmp_path / f"{prefix}_review.xlsx"),
        "recommended_next_action": "Review HIGH anomalies before approving payroll.",
    }
    manifest = {
        "agent_mode": "read_only_review",
        "review_id": "REV-1",
        "thresholds": {"variance_threshold": 20.0},
        "file_hashes": {
            "current_file_sha256": "a" * 64,
            "previous_file_sha256": "b" * 64,
            "review_workbook_sha256": "c" * 64,
            "summary_json_sha256": "d" * 64,
            "receipt_json_sha256": "e" * 64,
        },
    }

    (tmp_path / f"{prefix}_review.xlsx").write_bytes(b"PK")
    (tmp_path / f"{prefix}_summary.json").write_text("{}", encoding="utf-8")
    (tmp_path / f"{prefix}_receipt.json").write_text(
        json.dumps(receipt),
        encoding="utf-8",
    )
    (tmp_path / f"{prefix}_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    result = validate_review_outputs(tmp_path, prefix)

    assert result.ok is True
    assert result.errors == []


def test_review_output_validation_rejects_unsafe_receipt(tmp_path):
    prefix = "bad"
    receipt = {
        "agent_mode": "read_only_review",
        "human_action_required": True,
        "source_files_modified": True,
        "external_messages_sent": False,
        "approval_performed_by_agent": False,
        "review_id": "REV-1",
        "review_pack": str(tmp_path / f"{prefix}_review.xlsx"),
        "recommended_next_action": "Review blockers.",
    }

    (tmp_path / f"{prefix}_review.xlsx").write_bytes(b"PK")
    (tmp_path / f"{prefix}_summary.json").write_text("{}", encoding="utf-8")
    (tmp_path / f"{prefix}_receipt.json").write_text(
        json.dumps(receipt),
        encoding="utf-8",
    )
    (tmp_path / f"{prefix}_manifest.json").write_text(
        json.dumps({"agent_mode": "read_only_review", "review_id": "REV-1"}),
        encoding="utf-8",
    )

    result = validate_review_outputs(tmp_path, prefix)

    assert result.ok is False
    assert any("source_files_modified" in error for error in result.errors)
