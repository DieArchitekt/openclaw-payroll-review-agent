from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from processors.agent_controls_v1 import build_agent_receipt, review_gate
from processors.agent_controls_v1.constants import (
    BLOCKER_NO_CURRENT_ROWS,
    BLOCKER_NO_PREVIOUS_ROWS,
    RECOMMEND_HIGH_ANOMALIES,
    RECOMMEND_HUMAN_REVIEW,
    RECOMMEND_REVIEW_BLOCKERS,
)
from processors.agent_controls_v1.receipt import (
    RUN_STATUS_BLOCKED,
    RUN_STATUS_COMPLETED_WITH_EXCEPTIONS,
)
from processors.approval_workflow_v1 import create_approval_record
from processors.openclaw_reporting import AGENT_MODE_READ_ONLY_REVIEW
from processors.payroll_processor_v1.models import PayrollExtraction


def test_review_gate_blocks_empty_extractions_and_high_anomalies():
    result = SimpleNamespace(
        current_extraction=PayrollExtraction(rows=[]),
        previous_extraction=PayrollExtraction(rows=[]),
        anomalies_df=pd.DataFrame(
            [{"Severity": "HIGH"}, {"Severity": "HIGH"}, {"Severity": "MEDIUM"}]
        ),
    )

    gate = review_gate(result)

    assert gate["human_action_required"] is True
    assert gate["ready_for_review"] is False
    assert gate["ready_for_approval"] is False
    assert gate["high_anomaly_count"] == 2
    assert gate["medium_anomaly_count"] == 1
    assert BLOCKER_NO_CURRENT_ROWS in gate["blockers"]
    assert BLOCKER_NO_PREVIOUS_ROWS in gate["blockers"]
    assert "2 HIGH payroll anomalies require review." in gate["blockers"]
    assert gate["recommended_next_action"] == RECOMMEND_REVIEW_BLOCKERS


def test_review_gate_allows_human_review_when_no_blockers():
    result = SimpleNamespace(
        current_extraction=PayrollExtraction(rows=[{"Employee": "Ada Lovelace"}]),
        previous_extraction=PayrollExtraction(rows=[{"Employee": "Ada Lovelace"}]),
        anomalies_df=pd.DataFrame([{"Severity": "MEDIUM"}]),
    )

    gate = review_gate(result)

    assert gate["human_action_required"] is True
    assert gate["ready_for_review"] is True
    assert gate["ready_for_approval"] is False
    assert gate["high_anomaly_count"] == 0
    assert gate["medium_anomaly_count"] == 1
    assert gate["blockers"] == []
    assert gate["recommended_next_action"] == RECOMMEND_HUMAN_REVIEW


def test_agent_receipt_uses_read_only_contract():
    result = SimpleNamespace(
        current_extraction=PayrollExtraction(rows=[{"Employee": "Ada Lovelace"}]),
        previous_extraction=PayrollExtraction(rows=[{"Employee": "Ada Lovelace"}]),
        anomalies_df=pd.DataFrame([{"Severity": "HIGH"}, {"Severity": "MEDIUM"}]),
        approval_record=create_approval_record("OpenClaw"),
        review_workbook_bytes=b"workbook",
    )

    receipt = build_agent_receipt(
        result,
        Path("outputs/reviews/client-a_2026-05_review.xlsx"),
        Path("outputs/reviews/client-a_2026-05_summary.json"),
    )

    assert receipt["agent_mode"] == AGENT_MODE_READ_ONLY_REVIEW
    assert receipt["human_action_required"] is True
    assert receipt["source_files_modified"] is False
    assert receipt["external_messages_sent"] is False
    assert receipt["approval_performed_by_agent"] is False
    assert receipt["run_status"] == RUN_STATUS_COMPLETED_WITH_EXCEPTIONS
    assert receipt["recommended_next_action"] == RECOMMEND_HIGH_ANOMALIES
    assert receipt["high_anomaly_count"] == 1
    assert receipt["medium_anomaly_count"] == 1
    assert receipt["total_anomaly_count"] == 2
    assert receipt["ready_for_approval"] is False
    assert receipt["critical_controls"]["required_fields_mapped"] is True
    assert receipt["critical_controls"]["review_pack_generated"] is True
    assert receipt["critical_controls"]["high_anomalies_present"] is True


def test_agent_receipt_blocks_empty_extraction():
    result = SimpleNamespace(
        current_extraction=PayrollExtraction(rows=[]),
        previous_extraction=PayrollExtraction(rows=[]),
        anomalies_df=pd.DataFrame(),
        approval_record=create_approval_record("OpenClaw"),
        review_workbook_bytes=b"",
    )

    receipt = build_agent_receipt(result, Path("review.xlsx"), None)

    assert receipt["run_status"] == RUN_STATUS_BLOCKED
    assert receipt["ready_for_review"] is False
    assert receipt["ready_for_approval"] is False
    assert BLOCKER_NO_CURRENT_ROWS in receipt["blockers"]
    assert BLOCKER_NO_PREVIOUS_ROWS in receipt["blockers"]
    assert receipt["critical_controls"]["required_fields_mapped"] is False
    assert receipt["critical_controls"]["review_pack_generated"] is False
