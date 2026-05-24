import pytest

from processors.agent_controls_v1.confirmations import HumanConfirmation
from processors.agent_controls_v1.thresholds import (
    ThresholdChange,
    apply_threshold_change,
    default_thresholds,
)
from processors.audit_log_v1 import audit_log_path


def test_threshold_change_requires_confirmation_and_writes_audit(tmp_path):
    review_id = "REV-THRESHOLD"
    thresholds = default_thresholds(20.0)
    change = ThresholdChange(
        review_id=review_id,
        threshold_name="variance_threshold",
        old_value=20.0,
        new_value=15.0,
        reason="Month-end review tolerance was reduced.",
    )

    with pytest.raises(PermissionError):
        apply_threshold_change(thresholds, change, None, audit_root=tmp_path)

    confirmation = HumanConfirmation(
        action="change_thresholds",
        review_id=review_id,
        user_name="Finance Manager",
        reason="Approved threshold change.",
    )
    updated = apply_threshold_change(
        thresholds,
        change,
        confirmation,
        audit_root=tmp_path,
    )

    assert updated["variance_threshold"] == 15.0
    assert audit_log_path(review_id, tmp_path).exists()
