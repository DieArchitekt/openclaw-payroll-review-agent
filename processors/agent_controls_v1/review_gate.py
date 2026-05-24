from typing import Any

import pandas as pd

from processors.agent_controls_v1.constants import (
    BLOCKER_NO_CURRENT_ROWS,
    BLOCKER_NO_PREVIOUS_ROWS,
    RECOMMEND_HUMAN_REVIEW,
    RECOMMEND_REVIEW_BLOCKERS,
)
from processors.payroll_review_workflow import PayrollReviewResult


def review_gate(result: PayrollReviewResult) -> dict[str, object]:
    """Return the safe review status an automation agent is allowed to use."""
    high_count = severity_count(result.anomalies_df, "HIGH")
    medium_count = severity_count(result.anomalies_df, "MEDIUM")
    blockers = review_blockers(result, high_count)

    return {
        "human_action_required": True,
        "ready_for_review": not blockers,
        "ready_for_approval": False,
        "high_anomaly_count": high_count,
        "medium_anomaly_count": medium_count,
        "blockers": blockers,
        "recommended_next_action": (
            RECOMMEND_REVIEW_BLOCKERS if blockers else RECOMMEND_HUMAN_REVIEW
        ),
    }


def review_blockers(result: PayrollReviewResult, high_count: int) -> list[str]:
    """Return blocker messages that prevent an agent from calling a review clear."""
    blockers: list[str] = []

    if not result.current_extraction.rows:
        blockers.append(BLOCKER_NO_CURRENT_ROWS)

    if not result.previous_extraction.rows:
        blockers.append(BLOCKER_NO_PREVIOUS_ROWS)

    if high_count:
        blockers.append(f"{high_count} HIGH payroll anomalies require review.")

    return blockers


def severity_count(anomalies_df: pd.DataFrame, severity: str) -> int:
    """Return the number of anomalies for a severity label."""
    if anomalies_df.empty or "Severity" not in anomalies_df.columns:
        return 0

    return int((anomalies_df["Severity"] == severity).sum())
