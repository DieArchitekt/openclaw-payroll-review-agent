import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class AuditEvent:
    review_id: str
    action: str
    actor_type: str
    actor_name: str
    result: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    inputs_summary: dict[str, Any] = field(default_factory=dict)
    affected_file_names: list[str] = field(default_factory=list)
    old_status: str = ""
    new_status: str = ""
    error: str = ""
    confirmation_id: str = ""


def append_audit_event(
    review_id: str,
    *,
    action: str,
    actor_type: str,
    actor_name: str,
    result: str,
    output_root: Path = Path("outputs/audit"),
    inputs_summary: dict[str, Any] | None = None,
    affected_file_names: list[str] | None = None,
    old_status: str = "",
    new_status: str = "",
    error: str = "",
    confirmation_id: str = "",
) -> AuditEvent:
    event = AuditEvent(
        review_id=review_id,
        action=action,
        actor_type=actor_type,
        actor_name=actor_name,
        result=result,
        inputs_summary=inputs_summary or {},
        affected_file_names=affected_file_names or [],
        old_status=old_status,
        new_status=new_status,
        error=error,
        confirmation_id=confirmation_id,
    )
    path = audit_log_path(review_id, output_root)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), sort_keys=True))
        handle.write("\n")

    return event


def audit_log_path(review_id: str, output_root: Path = Path("outputs/audit")) -> Path:
    safe_review_id = "".join(
        character for character in review_id if character.isalnum() or character in "-_"
    )

    if not safe_review_id:
        raise ValueError("Review id is required for audit logging.")

    return output_root / f"{safe_review_id}.jsonl"
