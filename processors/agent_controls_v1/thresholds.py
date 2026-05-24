from dataclasses import dataclass
from pathlib import Path

from processors.agent_controls_v1.confirmations import (
    HumanConfirmation,
    validate_human_confirmation,
)
from processors.audit_log_v1 import append_audit_event
from processors.payroll_review_thresholds import (
    PROTECTED_THRESHOLDS,
    THRESHOLD_BACS_TOLERANCE,
    THRESHOLD_HIGH_NET_PAY,
    THRESHOLD_LOW_NI_RATIO,
    THRESHOLD_LOW_PAYE_RATIO,
    THRESHOLD_VARIANCE,
    default_thresholds,
)


@dataclass(frozen=True, slots=True)
class ThresholdChange:
    review_id: str
    threshold_name: str
    old_value: float
    new_value: float
    reason: str


def apply_threshold_change(
    thresholds: dict[str, float],
    change: ThresholdChange,
    confirmation: HumanConfirmation | None,
    *,
    audit_root: Path = Path("outputs/audit"),
) -> dict[str, float]:
    validate_threshold_change(change, confirmation)
    updated = dict(thresholds)
    updated[change.threshold_name] = float(change.new_value)
    append_audit_event(
        change.review_id,
        action="change_thresholds",
        actor_type="human",
        actor_name=confirmation.user_name if confirmation else "",
        result="completed",
        output_root=audit_root,
        inputs_summary={
            "threshold_name": change.threshold_name,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "reason": change.reason,
        },
        confirmation_id=confirmation.confirmation_id if confirmation else "",
    )
    return updated


def validate_threshold_change(
    change: ThresholdChange,
    confirmation: HumanConfirmation | None,
) -> None:
    if change.threshold_name not in PROTECTED_THRESHOLDS:
        raise ValueError(f"Unknown protected threshold: {change.threshold_name}")

    if change.new_value < 0:
        raise ValueError("Threshold values cannot be negative.")

    if not change.reason.strip():
        raise ValueError("Threshold change requires a reason.")

    validate_human_confirmation(
        confirmation,
        action="change_thresholds",
        review_id=change.review_id,
    )
