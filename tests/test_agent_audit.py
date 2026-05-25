import json

import pytest

from processors.agent_controls_v1.guard import GuardContext, run_guarded_agent_action
from processors.agent_controls_v1.safe_paths import resolve_agent_path
from processors.audit_log_v1 import append_audit_event, audit_log_path


def test_safe_paths_block_absolute_and_parent_traversal(tmp_path):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    valid_path = resolve_agent_path(
        "outputs/reviews/review.xlsx",
        repo_root=tmp_path,
    )

    assert valid_path == output_dir / "reviews" / "review.xlsx"

    with pytest.raises(ValueError, match="absolute"):
        resolve_agent_path(output_dir / "review.xlsx", repo_root=tmp_path)

    with pytest.raises(ValueError, match="repository root"):
        resolve_agent_path("../outside.xlsx", repo_root=tmp_path)

    with pytest.raises(ValueError, match="under"):
        resolve_agent_path("incoming_payroll/current.pdf", repo_root=tmp_path)


def test_audit_log_appends_jsonl_events(tmp_path):
    append_audit_event(
        "REV-1",
        action="agent_get_receipt",
        actor_type="agent",
        actor_name="OpenClaw",
        result="completed",
        output_root=tmp_path,
    )
    append_audit_event(
        "REV-1",
        action="agent_get_exception_summary",
        actor_type="agent",
        actor_name="OpenClaw",
        result="completed",
        output_root=tmp_path,
    )

    lines = audit_log_path("REV-1", tmp_path).read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert json.loads(lines[0])["action"] == "agent_get_receipt"
    assert json.loads(lines[1])["action"] == "agent_get_exception_summary"


def test_guarded_action_writes_started_and_completed_audit_events(tmp_path):
    context = GuardContext(
        review_id="REV-2",
        audit_root=tmp_path / "audit",
        repo_root=tmp_path,
    )
    (tmp_path / "outputs").mkdir()

    result = run_guarded_agent_action(
        "agent_get_receipt",
        context,
        lambda: {"ok": True},
        paths=("outputs/receipt.json",),
    )

    lines = (
        audit_log_path("REV-2", tmp_path / "audit")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert result == {"ok": True}
    assert [json.loads(line)["result"] for line in lines] == [
        "started",
        "completed",
    ]


def test_guarded_action_blocks_bad_path(tmp_path):
    context = GuardContext(review_id="REV-3", repo_root=tmp_path)

    with pytest.raises(ValueError, match="under"):
        run_guarded_agent_action(
            "agent_get_receipt",
            context,
            lambda: {"ok": True},
            paths=("incoming_payroll/receipt.json",),
        )
