import json
from pathlib import Path

import pytest

from processors.cli_paths import output_prefix
from processors.openclaw_reporting import ACTIVE_AGENT_MODE, AGENT_MODE_READ_ONLY_REVIEW
from processors.payroll_review_cli_runner import (
    cli_failure_message,
    run_cli,
    supported_file_types,
)
from tests.payroll_test_helpers import write_basic_payroll_pair


def test_full_review_cli_writes_workbook_and_summary_json(tmp_path):
    current = tmp_path / "current.csv"
    previous = tmp_path / "previous.csv"
    output = tmp_path / "review.xlsx"
    summary_json = tmp_path / "summary.json"
    receipt_json = tmp_path / "receipt.json"
    manifest_json = tmp_path / "review_manifest.json"
    write_basic_payroll_pair(current, previous)

    exit_code = run_cli(
        [
            str(current),
            str(previous),
            "--out",
            str(output),
            "--summary-json",
            str(summary_json),
            "--agent-receipt-json",
            str(receipt_json),
            "--prepared-by",
            "OpenClaw",
        ]
    )

    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_json.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert output.exists()
    assert output.read_bytes().startswith(b"PK")
    assert receipt_json.exists()
    assert manifest_json.exists()
    assert payload["approval_status"] == "Prepared"
    assert payload["agent_mode"] == AGENT_MODE_READ_ONLY_REVIEW
    assert payload["agent_receipt_json"] == str(receipt_json)
    assert payload["run_status"] == receipt["run_status"]
    assert payload["recommended_next_action"] == receipt["recommended_next_action"]
    assert receipt["human_action_required"] is True
    assert len(receipt["file_hashes"]["current_file_sha256"]) == 64
    assert len(receipt["file_hashes"]["previous_file_sha256"]) == 64
    assert len(receipt["file_hashes"]["review_workbook_sha256"]) == 64
    assert len(receipt["file_hashes"]["summary_json_sha256"]) == 64
    assert (
        payload["file_hashes"]["current_file_sha256"]
        == receipt["file_hashes"]["current_file_sha256"]
    )
    assert payload["run_manifest_json"] == str(manifest_json)
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["review_id"] == payload["review_id"]
    assert len(manifest["file_hashes"]["receipt_json_sha256"]) == 64
    assert payload["prepared_by"] == "OpenClaw"
    assert payload["current_file"] == "current.csv"


def test_full_review_cli_print_json_outputs_machine_readable_summary(tmp_path, capsys):
    current = tmp_path / "current.csv"
    previous = tmp_path / "previous.csv"
    output = tmp_path / "review.xlsx"
    summary_json = tmp_path / "summary.json"
    write_basic_payroll_pair(current, previous)

    exit_code = run_cli(
        [
            str(current),
            str(previous),
            "--out",
            str(output),
            "--summary-json",
            str(summary_json),
            "--print-json",
            "--prepared-by",
            "OpenClaw",
        ]
    )

    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(summary_json.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert stdout_payload["approval_status"] == "Prepared"
    assert stdout_payload["agent_mode"] == ACTIVE_AGENT_MODE
    assert stdout_payload["review_id"] == file_payload["review_id"]
    assert output.exists()


def test_output_prefix_falls_back_to_timestamp_when_name_has_no_period():
    prefix = output_prefix(Path("current.csv"))

    assert prefix.startswith("payroll_review_")


def test_cli_rejects_unsupported_explicit_input_file(tmp_path):
    current = tmp_path / "current.docx"
    previous = tmp_path / "previous.csv"
    current.write_text("not supported", encoding="utf-8")
    previous.write_text("Employee,NetPay\nAda Lovelace,2350\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        run_cli([str(current), str(previous)])

    assert "unsupported file type" in str(exc.value)
    assert supported_file_types() in str(exc.value)


def test_cli_failure_message_is_short_and_non_destructive():
    message = cli_failure_message("Current payroll file not found: missing.csv")

    assert "Payroll review failed." in message
    assert "Current payroll file not found" in message
    assert "No files were moved" in message
