from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from processors.agent_controls_v1.actions import AgentAction, get_agent_action
from processors.agent_controls_v1.confirmations import (
    HumanConfirmation,
    validate_human_confirmation,
)
from processors.agent_controls_v1.permissions import check_permission
from processors.agent_controls_v1.safe_paths import resolve_agent_path
from processors.audit_log_v1 import append_audit_event


@dataclass(frozen=True, slots=True)
class GuardContext:
    review_id: str
    actor_name: str = "OpenClaw"
    audit_root: Path = Path("outputs/audit")
    repo_root: Path | None = None


def run_guarded_agent_action(
    action_name: str,
    context: GuardContext,
    executor: Callable[[], Any],
    *,
    confirmation: HumanConfirmation | None = None,
    paths: tuple[str | Path, ...] = (),
) -> Any:
    action = get_agent_action(action_name)
    validate_action(action, context, confirmation, paths)

    append_audit_event(
        context.review_id,
        action=action.name,
        actor_type="agent",
        actor_name=context.actor_name,
        result="started",
        output_root=context.audit_root,
        inputs_summary={"paths": [str(path) for path in paths]},
    )

    try:
        result = executor()
    except Exception as exc:
        append_audit_event(
            context.review_id,
            action=action.name,
            actor_type="agent",
            actor_name=context.actor_name,
            result="failed",
            error=str(exc),
            output_root=context.audit_root,
        )
        raise

    append_audit_event(
        context.review_id,
        action=action.name,
        actor_type="agent",
        actor_name=context.actor_name,
        result="completed",
        output_root=context.audit_root,
        confirmation_id=confirmation.confirmation_id if confirmation else "",
    )
    return result


def validate_action(
    action: AgentAction,
    context: GuardContext,
    confirmation: HumanConfirmation | None = None,
    paths: tuple[str | Path, ...] = (),
) -> None:
    permission = check_permission(
        action.permission,
        confirmed=bool(confirmation),
    )

    if not permission.allowed:
        raise PermissionError(permission.reason)

    if action.external_transmission:
        raise PermissionError("External transmission is not allowed in read-only mode.")

    if action.requires_confirmation:
        validate_human_confirmation(
            confirmation,
            action=action.name,
            review_id=context.review_id,
        )

    for path in paths:
        resolve_agent_path(path, repo_root=context.repo_root)
