from dataclasses import dataclass

ALLOW = "allow"
DENY = "deny"
CONFIRM = "confirm"

PERMISSION_READ_UPLOADED_FILES = "read_uploaded_files"
PERMISSION_RUN_PAYROLL_REVIEW = "run_payroll_review"
PERMISSION_GENERATE_REVIEW_PACK = "generate_review_pack"
PERMISSION_READ_SUMMARY_JSON = "read_summary_json"
PERMISSION_READ_AGENT_RECEIPT = "read_agent_receipt"
PERMISSION_DRAFT_COMMENTS = "draft_comments"
PERMISSION_UPDATE_REVIEW_NOTES = "update_review_notes"
PERMISSION_APPROVE_REVIEW = "approve_review"
PERMISSION_REJECT_REVIEW = "reject_review"
PERMISSION_MARK_EXPORTED = "mark_exported"
PERMISSION_SEND_EXTERNAL_FILE = "send_external_file"
PERMISSION_DELETE_FILE = "delete_file"
PERMISSION_MOVE_SOURCE_FILE = "move_source_file"
PERMISSION_CHANGE_THRESHOLDS = "change_thresholds"


@dataclass(frozen=True, slots=True)
class PermissionRule:
    permission: str
    effect: str
    requires_confirmation: bool = False


@dataclass(frozen=True, slots=True)
class PermissionCheck:
    permission: str
    allowed: bool
    requires_confirmation: bool
    reason: str


def default_permission_rules() -> dict[str, PermissionRule]:
    return {
        PERMISSION_READ_UPLOADED_FILES: PermissionRule(
            PERMISSION_READ_UPLOADED_FILES, ALLOW
        ),
        PERMISSION_RUN_PAYROLL_REVIEW: PermissionRule(
            PERMISSION_RUN_PAYROLL_REVIEW, ALLOW
        ),
        PERMISSION_GENERATE_REVIEW_PACK: PermissionRule(
            PERMISSION_GENERATE_REVIEW_PACK, ALLOW
        ),
        PERMISSION_READ_SUMMARY_JSON: PermissionRule(
            PERMISSION_READ_SUMMARY_JSON, ALLOW
        ),
        PERMISSION_READ_AGENT_RECEIPT: PermissionRule(
            PERMISSION_READ_AGENT_RECEIPT, ALLOW
        ),
        PERMISSION_DRAFT_COMMENTS: PermissionRule(PERMISSION_DRAFT_COMMENTS, ALLOW),
        PERMISSION_UPDATE_REVIEW_NOTES: PermissionRule(
            PERMISSION_UPDATE_REVIEW_NOTES, CONFIRM, True
        ),
        PERMISSION_CHANGE_THRESHOLDS: PermissionRule(
            PERMISSION_CHANGE_THRESHOLDS, CONFIRM, True
        ),
        PERMISSION_APPROVE_REVIEW: PermissionRule(
            PERMISSION_APPROVE_REVIEW, DENY, True
        ),
        PERMISSION_REJECT_REVIEW: PermissionRule(PERMISSION_REJECT_REVIEW, DENY, True),
        PERMISSION_MARK_EXPORTED: PermissionRule(PERMISSION_MARK_EXPORTED, DENY, True),
        PERMISSION_SEND_EXTERNAL_FILE: PermissionRule(
            PERMISSION_SEND_EXTERNAL_FILE, DENY, True
        ),
        PERMISSION_DELETE_FILE: PermissionRule(PERMISSION_DELETE_FILE, DENY, True),
        PERMISSION_MOVE_SOURCE_FILE: PermissionRule(
            PERMISSION_MOVE_SOURCE_FILE, DENY, True
        ),
    }


def check_permission(
    permission: str,
    *,
    confirmed: bool = False,
    rules: dict[str, PermissionRule] | None = None,
) -> PermissionCheck:
    rule = (rules or default_permission_rules()).get(permission)

    if not rule:
        return PermissionCheck(permission, False, False, "Permission is not listed.")

    if rule.effect == ALLOW:
        return PermissionCheck(permission, True, False, "Permission allowed.")

    if rule.effect == CONFIRM:
        if confirmed:
            return PermissionCheck(
                permission, True, True, "Human confirmation supplied."
            )

        return PermissionCheck(permission, False, True, "Human confirmation required.")

    return PermissionCheck(
        permission, False, rule.requires_confirmation, "Permission denied."
    )
