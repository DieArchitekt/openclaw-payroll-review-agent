import pytest

from processors.approval_workflow_v1 import (
    STATUS_APPROVED,
    STATUS_EXPORTED,
    STATUS_PREPARED,
    STATUS_QUERIES_RAISED,
    STATUS_REJECTED,
    STATUS_REVIEWED,
    approve_review,
    create_approval_record,
    mark_exported,
    mark_reviewed,
    raise_queries,
    reject_review,
)


def test_approval_transitions_allow_expected_flow():
    record = create_approval_record("preparer")

    mark_reviewed(record, "reviewer", "looks fine")
    assert record.status == STATUS_REVIEWED
    assert record.reviewed_by == "reviewer"
    assert record.reviewer_comments == "looks fine"

    approve_review(record, "approver", "approved")
    assert record.status == STATUS_APPROVED
    assert record.approved_by == "approver"
    assert record.approval_comments == "approved"

    mark_exported(record, "exporter")
    assert record.status == STATUS_EXPORTED
    assert record.exported_by == "exporter"


def test_approval_queries_can_return_to_reviewed():
    record = create_approval_record("preparer")

    raise_queries(record, "reviewer", "missing explanation")
    assert record.status == STATUS_QUERIES_RAISED
    assert record.query_notes == "missing explanation"

    mark_reviewed(record, "reviewer", "query resolved")
    assert record.status == STATUS_REVIEWED
    assert record.reviewer_comments == "query resolved"


def test_approval_invalid_transitions_are_blocked():
    prepared = create_approval_record("preparer")

    with pytest.raises(ValueError):
        approve_review(prepared, "approver")

    rejected = create_approval_record("preparer")
    mark_reviewed(rejected, "reviewer")
    reject_review(rejected, "approver", "not acceptable")
    assert rejected.status == STATUS_REJECTED

    with pytest.raises(ValueError):
        mark_exported(rejected, "exporter")
