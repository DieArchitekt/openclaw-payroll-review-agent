import json
from pathlib import Path

import pytest

from processors.cli_paths import output_prefix
from processors.openclaw_file_pairing import (
    discover_payroll_pairs,
    find_payroll_pair,
    is_supported_payroll_file,
    wait_for_stable_payroll_pair,
)
from processors.openclaw_reporting import (
    ACTIVE_AGENT_MODE,
    AGENT_MODE_READ_ONLY_REVIEW,
    review_completion_message,
)
from processors.payroll_review_cli import (
    cli_failure_message,
    run_cli,
    supported_file_types,
)


def write_basic_payroll_pair(current: Path, previous: Path) -> None:
    current.write_text(
        "Employee,GrossPay,PAYE,EmployeeNI,NetPay,EmployerNI,EmployerPension\n"
        "Ada Lovelace,3000,400,250,2350,300,150\n",
        encoding="utf-8",
    )
    previous.write_text(
        "Employee,GrossPay,PAYE,EmployeeNI,NetPay,EmployerNI,EmployerPension\n"
        "Ada Lovelace,2900,390,240,2300,290,145\n",
        encoding="utf-8",
    )


def test_full_review_cli_writes_workbook_and_summary_json(tmp_path):
    current = tmp_path / "current.csv"
    previous = tmp_path / "previous.csv"
    output = tmp_path / "review.xlsx"
    summary_json = tmp_path / "summary.json"
    receipt_json = tmp_path / "receipt.json"
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
    assert payload["approval_status"] == "Prepared"
    assert payload["agent_mode"] == AGENT_MODE_READ_ONLY_REVIEW
    assert payload["agent_receipt_json"] == str(receipt_json)
    assert receipt["agent_mode"] == AGENT_MODE_READ_ONLY_REVIEW
    assert receipt["human_action_required"] is True
    assert receipt["source_files_modified"] is False
    assert receipt["external_messages_sent"] is False
    assert receipt["approval_performed_by_agent"] is False
    assert payload["prepared_by"] == "OpenClaw"
    assert payload["current_file"] == "current.csv"


def test_openclaw_folder_pairing_discovers_matching_current_previous_files(tmp_path):
    current_dir = tmp_path / "current"
    previous_dir = tmp_path / "previous"
    current_dir.mkdir()
    previous_dir.mkdir()
    current_file = current_dir / "client-a_2026-05_current.csv"
    previous_file = previous_dir / "client-a_2026-04_previous.csv"
    current_file.write_text("current", encoding="utf-8")
    previous_file.write_text("previous", encoding="utf-8")

    pair = find_payroll_pair(tmp_path)

    assert pair.key == "client-a"
    assert pair.current_path == current_file
    assert pair.previous_path == previous_file
    assert discover_payroll_pairs(tmp_path) == [pair]


def test_full_review_cli_can_use_incoming_root(tmp_path):
    incoming = tmp_path / "incoming_payroll"
    current_dir = incoming / "current"
    previous_dir = incoming / "previous"
    current_dir.mkdir(parents=True)
    previous_dir.mkdir(parents=True)
    output = tmp_path / "review.xlsx"
    summary_json = tmp_path / "summary.json"
    write_basic_payroll_pair(
        current_dir / "payroll_current.csv",
        previous_dir / "payroll_previous.csv",
    )

    exit_code = run_cli(
        [
            "--incoming-root",
            str(incoming),
            "--out",
            str(output),
            "--summary-json",
            str(summary_json),
            "--prepared-by",
            "OpenClaw",
        ]
    )

    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert output.exists()
    assert payload["current_file"] == "payroll_current.csv"
    assert payload["previous_file"] == "payroll_previous.csv"


def test_full_review_cli_incoming_root_writes_openclaw_contract_outputs(tmp_path):
    incoming = tmp_path / "incoming_payroll"
    current_dir = incoming / "current"
    previous_dir = incoming / "previous"
    output_dir = tmp_path / "reviews"
    current_dir.mkdir(parents=True)
    previous_dir.mkdir(parents=True)
    write_basic_payroll_pair(
        current_dir / "client-a_2026-05_current.csv",
        previous_dir / "client-a_2026-04_previous.csv",
    )

    exit_code = run_cli(
        [
            "--incoming-root",
            str(incoming),
            "--output-dir",
            str(output_dir),
            "--prepared-by",
            "OpenClaw",
        ]
    )

    review_pack = output_dir / "client-a_2026-05_review.xlsx"
    summary_json = output_dir / "client-a_2026-05_summary.json"
    receipt_json = output_dir / "client-a_2026-05_receipt.json"
    summary = json.loads(summary_json.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_json.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert review_pack.exists()
    assert summary_json.exists()
    assert receipt_json.exists()
    assert summary["agent_receipt_json"] == str(receipt_json)
    assert receipt["agent_mode"] == AGENT_MODE_READ_ONLY_REVIEW
    assert receipt["human_action_required"] is True
    assert receipt["source_files_modified"] is False
    assert receipt["external_messages_sent"] is False
    assert receipt["approval_performed_by_agent"] is False


def test_wait_for_stable_payroll_pair_returns_existing_stable_pair(tmp_path):
    current_dir = tmp_path / "current"
    previous_dir = tmp_path / "previous"
    current_dir.mkdir()
    previous_dir.mkdir()
    current_file = current_dir / "payroll_current.csv"
    previous_file = previous_dir / "payroll_previous.csv"
    current_file.write_text("current", encoding="utf-8")
    previous_file.write_text("previous", encoding="utf-8")

    pair = wait_for_stable_payroll_pair(
        tmp_path,
        timeout_seconds=1,
        poll_interval_seconds=0.01,
        stable_checks=1,
    )

    assert pair.current_path == current_file
    assert pair.previous_path == previous_file


def test_openclaw_pairing_rejects_missing_previous_file(tmp_path):
    current_dir = tmp_path / "current"
    previous_dir = tmp_path / "previous"
    current_dir.mkdir()
    previous_dir.mkdir()
    (current_dir / "client-a_2026-05_current.csv").write_text(
        "current",
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        find_payroll_pair(tmp_path)


def test_openclaw_pairing_rejects_multiple_pairs(tmp_path):
    current_dir = tmp_path / "current"
    previous_dir = tmp_path / "previous"
    current_dir.mkdir()
    previous_dir.mkdir()

    for client in ("client-a", "client-b"):
        (current_dir / f"{client}_2026-05_current.csv").write_text(
            "current",
            encoding="utf-8",
        )
        (previous_dir / f"{client}_2026-04_previous.csv").write_text(
            "previous",
            encoding="utf-8",
        )

    with pytest.raises(ValueError):
        find_payroll_pair(tmp_path)


def test_openclaw_pairing_rejects_unsupported_file_type(tmp_path):
    source = tmp_path / "payroll_current.docx"
    source.write_text("not supported", encoding="utf-8")

    assert is_supported_payroll_file(source) is False


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


def test_output_prefix_falls_back_to_timestamp_when_name_has_no_period():
    prefix = output_prefix(Path("current.csv"))

    assert prefix.startswith("payroll_review_")


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
    assert "Human review is required before approval/export." in message
    assert "12345.67" not in message
    assert "client-a_2026-05_current.csv" not in message


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
