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
