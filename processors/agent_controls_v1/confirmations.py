from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class HumanConfirmation:
    action: str
    review_id: str
    user_name: str
    reason: str
    receipt_hash: str = ""
    confirmation_id: str = field(default_factory=lambda: str(uuid4()))
    confirmed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    actor_type: str = "human"


def validate_human_confirmation(
    confirmation: HumanConfirmation | None,
    *,
    action: str,
    review_id: str,
) -> HumanConfirmation:
    if confirmation is None:
        raise PermissionError("Human confirmation is required.")

    if confirmation.actor_type != "human":
        raise PermissionError("Confirmation must come from a human actor.")

    if confirmation.action != action:
        raise PermissionError("Confirmation action does not match requested action.")

    if confirmation.review_id != review_id:
        raise PermissionError("Confirmation review id does not match requested review.")

    if not confirmation.user_name.strip():
        raise PermissionError("Confirmation requires a user name.")

    if not confirmation.reason.strip():
        raise PermissionError("Confirmation requires a reason.")

    return confirmation
