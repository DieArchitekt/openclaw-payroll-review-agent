from dataclasses import dataclass

from processors.agent_controls_v1.permissions import (
    PERMISSION_DRAFT_COMMENTS,
    PERMISSION_GENERATE_REVIEW_PACK,
    PERMISSION_READ_AGENT_RECEIPT,
    PERMISSION_RUN_PAYROLL_REVIEW,
)

RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"


@dataclass(frozen=True, slots=True)
class AgentAction:
    name: str
    permission: str
    risk_level: str
    reads_files: bool
    writes_files: bool
    requires_confirmation: bool
    external_transmission: bool


def action_registry() -> dict[str, AgentAction]:
    return {
        "agent_run_review": AgentAction(
            "agent_run_review",
            PERMISSION_RUN_PAYROLL_REVIEW,
            RISK_MEDIUM,
            reads_files=True,
            writes_files=True,
            requires_confirmation=False,
            external_transmission=False,
        ),
        "agent_get_receipt": AgentAction(
            "agent_get_receipt",
            PERMISSION_READ_AGENT_RECEIPT,
            RISK_LOW,
            reads_files=True,
            writes_files=False,
            requires_confirmation=False,
            external_transmission=False,
        ),
        "agent_get_exception_summary": AgentAction(
            "agent_get_exception_summary",
            PERMISSION_GENERATE_REVIEW_PACK,
            RISK_LOW,
            reads_files=False,
            writes_files=False,
            requires_confirmation=False,
            external_transmission=False,
        ),
        "agent_draft_review_comment": AgentAction(
            "agent_draft_review_comment",
            PERMISSION_DRAFT_COMMENTS,
            RISK_LOW,
            reads_files=False,
            writes_files=False,
            requires_confirmation=False,
            external_transmission=False,
        ),
    }


def get_agent_action(name: str) -> AgentAction:
    action = action_registry().get(name)

    if not action:
        raise ValueError(f"Agent action is not registered: {name}")

    return action


def is_registered_action(name: str) -> bool:
    return name in action_registry()
