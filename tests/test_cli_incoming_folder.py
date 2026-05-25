import json

import pytest

from processors.openclaw_file_pairing import (
    discover_payroll_pairs,
    find_payroll_pair,
    is_supported_payroll_file,
    wait_for_stable_payroll_pair,
)
from processors.payroll_review_cli_runner import run_cli
from tests.payroll_test_helpers import write_basic_payroll_pair


def test_openclaw_folder_pairing_discovers_flat_current_previous_files(tmp_path):
    current_file = tmp_path / "current.csv"
    previous_file = tmp_path / "previous.csv"
    current_file.write_text("current", encoding="utf-8")
    previous_file.write_text("previous", encoding="utf-8")

    pair = find_payroll_pair(tmp_path)

    assert pair.key == "incoming_payroll"
    assert pair.current_path == current_file
    assert pair.previous_path == previous_file
    assert discover_payroll_pairs(tmp_path) == [pair]


def test_full_review_cli_can_use_incoming_root(tmp_path):
    incoming = tmp_path / "incoming_payroll"
    incoming.mkdir()
    output = tmp_path / "review.xlsx"
    summary_json = tmp_path / "summary.json"
    write_basic_payroll_pair(
        incoming / "current.csv",
        incoming / "previous.csv",
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
    assert payload["current_file"] == "current.csv"
    assert payload["previous_file"] == "previous.csv"


def test_full_review_cli_defaults_to_incoming_payroll_folder(tmp_path, monkeypatch):
    incoming = tmp_path / "incoming_payroll"
    output = tmp_path / "review.xlsx"
    summary_json = tmp_path / "summary.json"
    incoming.mkdir()
    write_basic_payroll_pair(
        incoming / "current.csv",
        incoming / "previous.csv",
    )
    monkeypatch.chdir(tmp_path)

    exit_code = run_cli(
        [
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
    assert payload["current_file"] == "current.csv"
    assert payload["previous_file"] == "previous.csv"


def test_wait_for_stable_payroll_pair_returns_existing_stable_pair(tmp_path):
    current_file = tmp_path / "current.csv"
    previous_file = tmp_path / "previous.csv"
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
    (tmp_path / "current.csv").write_text(
        "current",
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError):
        find_payroll_pair(tmp_path)


def test_openclaw_pairing_rejects_unexpected_supported_files(tmp_path):
    (tmp_path / "current.csv").write_text("current", encoding="utf-8")
    (tmp_path / "previous.csv").write_text("previous", encoding="utf-8")
    (tmp_path / "extra.csv").write_text("extra", encoding="utf-8")

    with pytest.raises(ValueError):
        find_payroll_pair(tmp_path)


def test_openclaw_pairing_rejects_unsupported_file_type(tmp_path):
    source = tmp_path / "payroll_current.docx"
    source.write_text("not supported", encoding="utf-8")

    assert is_supported_payroll_file(source) is False
