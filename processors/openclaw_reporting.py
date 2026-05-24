from typing import Any

from processors.agent_controls_v1.constants import (
    ACTIVE_AGENT_MODE,
    AGENT_MODE_READ_ONLY_REVIEW,
)


def review_completion_message(payload: dict[str, Any]) -> str:
    """Return the safe completion message an automation agent can show users."""
    run_status = payload.get("run_status") or "completed"
    next_action = (
        payload.get("recommended_next_action")
        or "Human review is required before approval/export."
    )

    return "\n".join(
        [
            "Payroll review completed.",
            "",
            f"Review ID: {payload.get('review_id', '')}",
            f"Approval status: {payload.get('approval_status', '')}",
            f"Run status: {run_status}",
            f"Review pack: {payload.get('review_pack', '')}",
            f"High exceptions: {payload.get('high_exception_count', 0)}",
            f"Medium exceptions: {payload.get('medium_exception_count', 0)}",
            f"Total exceptions: {payload.get('exception_count', 0)}",
            "",
            f"Recommended next action: {next_action}",
        ]
    )
