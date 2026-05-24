from typing import Any

AGENT_MODE_READ_ONLY_REVIEW = "read_only_review"
ACTIVE_AGENT_MODE = AGENT_MODE_READ_ONLY_REVIEW


def review_completion_message(payload: dict[str, Any]) -> str:
    """Return the safe completion message an automation agent can show users."""
    return "\n".join(
        [
            "Payroll review completed.",
            "",
            f"Review ID: {payload.get('review_id', '')}",
            f"Approval status: {payload.get('approval_status', '')}",
            f"Review pack: {payload.get('review_pack', '')}",
            f"High exceptions: {payload.get('high_exception_count', 0)}",
            f"Medium exceptions: {payload.get('medium_exception_count', 0)}",
            f"Total exceptions: {payload.get('exception_count', 0)}",
            "",
            "Human review is required before approval/export.",
        ]
    )
