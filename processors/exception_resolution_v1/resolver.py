import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from processors.audit_log_v1 import append_audit_event

RESOLUTION_OPEN = "Open"
RESOLUTION_ACCEPTED = "Accepted"
RESOLUTION_RESOLVED = "Resolved"
RESOLUTION_STATUSES = {RESOLUTION_OPEN, RESOLUTION_ACCEPTED, RESOLUTION_RESOLVED}

RESOLUTION_COLUMNS = [
    "Anomaly ID",
    "Resolution Status",
    "Resolution Reason",
    "Resolved By",
    "Resolved At",
]


@dataclass(frozen=True, slots=True)
class ExceptionResolution:
    review_id: str
    anomaly_id: str
    status: str
    reason: str
    resolved_by: str
    resolved_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolution_id: str = field(default_factory=lambda: str(uuid4()))


def add_anomaly_ids(anomalies_df: pd.DataFrame) -> pd.DataFrame:
    if anomalies_df.empty:
        return ensure_resolution_columns(anomalies_df.copy())

    output = anomalies_df.copy()

    if "Anomaly ID" not in output.columns:
        output.insert(
            0, "Anomaly ID", [anomaly_id(row) for _, row in output.iterrows()]
        )

    return ensure_resolution_columns(output)


def apply_exception_resolutions(
    anomalies_df: pd.DataFrame,
    resolutions: list[ExceptionResolution],
    *,
    audit_root: Path = Path("outputs/audit"),
) -> pd.DataFrame:
    output = add_anomaly_ids(anomalies_df)
    resolution_map = {resolution.anomaly_id: resolution for resolution in resolutions}

    for index, row in output.iterrows():
        resolution = resolution_map.get(str(row["Anomaly ID"]))

        if not resolution:
            continue

        validate_resolution(resolution)
        output.at[index, "Resolution Status"] = resolution.status
        output.at[index, "Resolution Reason"] = resolution.reason
        output.at[index, "Resolved By"] = resolution.resolved_by
        output.at[index, "Resolved At"] = resolution.resolved_at.isoformat(
            timespec="seconds"
        )
        append_audit_event(
            resolution.review_id,
            action="resolve_exception",
            actor_type="human",
            actor_name=resolution.resolved_by,
            result="completed",
            output_root=audit_root,
            inputs_summary={
                "anomaly_id": resolution.anomaly_id,
                "status": resolution.status,
                "reason": resolution.reason,
            },
            confirmation_id=resolution.resolution_id,
        )

    return output


def anomaly_id(row: pd.Series | dict[str, Any]) -> str:
    values = [
        str(row.get("Severity", "")),
        str(row.get("Category", "")),
        str(row.get("Employee", "")),
        str(row.get("Field", "")),
        str(row.get("Message", "")),
    ]
    digest = hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()
    return digest[:16]


def ensure_resolution_columns(anomalies_df: pd.DataFrame) -> pd.DataFrame:
    output = anomalies_df.copy()

    if "Anomaly ID" not in output.columns:
        output.insert(0, "Anomaly ID", [])

    defaults = {
        "Resolution Status": RESOLUTION_OPEN,
        "Resolution Reason": "",
        "Resolved By": "",
        "Resolved At": "",
    }

    for column, default in defaults.items():
        if column not in output.columns:
            output[column] = default

    return output


def validate_resolution(resolution: ExceptionResolution) -> None:
    if resolution.status not in {RESOLUTION_ACCEPTED, RESOLUTION_RESOLVED}:
        raise ValueError("Exception resolution must be Accepted or Resolved.")

    if not resolution.reason.strip():
        raise ValueError("Exception resolution requires a reason.")

    if not resolution.resolved_by.strip():
        raise ValueError("Exception resolution requires a named reviewer.")
