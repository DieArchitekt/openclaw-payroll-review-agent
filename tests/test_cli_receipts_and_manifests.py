import json

from processors.openclaw_reporting import (
    AGENT_MODE_READ_ONLY_REVIEW,
    review_completion_message,
)
from processors.payroll_review_cli_runner import run_cli
from tests.payroll_test_helpers import write_basic_payroll_pair


def test_full_review_cli_incoming_root_writes_openclaw_contract_outputs(tmp_path):
    incoming = tmp_path / "incoming_payroll"
    output_dir = tmp_path / "reviews"
    incoming.mkdir()
    write_basic_payroll_pair(
        incoming / "current.csv",
        incoming / "previous.csv",
    )

    exit_code = run_cli(
        [
            "--incoming-root",
            str(incoming),
            "--output-dir",
            str(output_dir),
            "--output-prefix",
            "sample_incoming",
            "--prepared-by",
            "OpenClaw",
        ]
    )

    review_pack = output_dir / "sample_incoming_review.xlsx"
    summary_json = output_dir / "sample_incoming_summary.json"
    receipt_json = output_dir / "sample_incoming_receipt.json"
    manifest_json = output_dir / "sample_incoming_manifest.json"
    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_json.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert review_pack.exists()
    assert summary_json.exists()
    assert receipt_json.exists()
    assert manifest_json.exists()
    assert summary["agent_receipt_json"] == str(receipt_json)
    assert summary["run_manifest_json"] == str(manifest_json)
    assert receipt["agent_mode"] == AGENT_MODE_READ_ONLY_REVIEW
    assert receipt["human_action_required"] is True
    assert receipt["source_files_modified"] is False
    assert receipt["external_messages_sent"] is False
    assert receipt["approval_performed_by_agent"] is False


def test_cli_default_output_paths_are_named_and_do_not_overwrite(tmp_path):
    current = tmp_path / "client-a_2026-05_current.csv"
    previous = tmp_path / "client-a_2026-04_previous.csv"
    output_dir = tmp_path / "reviews"
    write_basic_payroll_pair(current, previous)

    first_exit_code = run_cli(
        [
            str(current),
            str(previous),
            "--output-dir",
            str(output_dir),
            "--prepared-by",
            "OpenClaw",
        ]
    )
    second_exit_code = run_cli(
        [
            str(current),
            str(previous),
            "--output-dir",
            str(output_dir),
            "--prepared-by",
            "OpenClaw",
        ]
    )

    review_packs = sorted(output_dir.glob("client-a_2026-05*_review.xlsx"))
    summaries = sorted(output_dir.glob("client-a_2026-05*_summary.json"))
    receipts = sorted(output_dir.glob("client-a_2026-05*_receipt.json"))
    assert first_exit_code == 0
    assert second_exit_code == 0
    assert len(review_packs) == 2
    assert len(summaries) == 2
    assert len(receipts) == 2
    assert review_packs[0].read_bytes().startswith(b"PK")


def test_openclaw_completion_message_is_redacted():
    payload = {
        "review_id": "REV-1",
        "approval_status": "Prepared",
        "review_pack": "outputs/reviews/client-a_2026-05_review.xlsx",
        "high_exception_count": 2,
        "medium_exception_count": 3,
        "exception_count": 5,
        "summary": {"current_total_net_pay": 12345.67},
        "current_file": "client-a_2026-05_current.csv",
    }

    message = review_completion_message(payload)

    assert "Review ID: REV-1" in message
    assert "High exceptions: 2" in message
    assert "Medium exceptions: 3" in message
    assert "Total exceptions: 5" in message
    assert "Run status: completed" in message
    assert (
        "Recommended next action: Human review is required before approval/export."
        in message
    )
    assert "12345.67" not in message
    assert "client-a_2026-05_current.csv" not in message


def test_openclaw_completion_message_reports_receipt_fields():
    payload = {
        "review_id": "REV-2",
        "approval_status": "Prepared",
        "review_pack": "outputs/reviews/review.xlsx",
        "high_exception_count": 1,
        "medium_exception_count": 0,
        "exception_count": 1,
        "run_status": "completed_with_exceptions",
        "recommended_next_action": "Review HIGH anomalies before approving payroll.",
    }

    message = review_completion_message(payload)

    assert "Run status: completed_with_exceptions" in message
    assert (
        "Recommended next action: Review HIGH anomalies before approving payroll."
        in message
    )
