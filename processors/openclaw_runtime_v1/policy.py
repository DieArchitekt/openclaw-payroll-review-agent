import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from processors.versioning import ACTIVE_AGENT_MODE

DEFAULT_POLICY_PATH = Path("openclaw/runtime_policy.json")
REQUIRED_INCOMING_DIRS = (
    Path("incoming_payroll/current"),
    Path("incoming_payroll/previous"),
)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def load_runtime_policy(
    policy_path: Path = DEFAULT_POLICY_PATH,
) -> dict[str, Any]:
    return json.loads(policy_path.read_text(encoding="utf-8"))


def validate_runtime_environment(
    repo_root: Path | None = None,
    policy_path: Path = DEFAULT_POLICY_PATH,
) -> ValidationResult:
    repo_root = (repo_root or Path.cwd()).resolve()
    policy_path = repo_root / policy_path
    errors: list[str] = []
    warnings: list[str] = []

    if not policy_path.exists():
        errors.append(f"Runtime policy not found: {policy_path}")
        return ValidationResult(False, errors, warnings)

    policy = load_runtime_policy(policy_path)

    if policy.get("agent_mode") != ACTIVE_AGENT_MODE:
        errors.append("Runtime policy must use read_only_review mode.")

    for folder in REQUIRED_INCOMING_DIRS:
        if not (repo_root / folder).exists():
            errors.append(f"Required incoming folder is missing: {folder}")

    for command in policy.get("allowed_commands", []):
        if not (repo_root / command).exists():
            errors.append(f"Allowed command does not exist: {command}")

    gitignore = repo_root / ".gitignore"

    if not gitignore.exists():
        warnings.append(".gitignore is missing.")
    else:
        gitignore_text = gitignore.read_text(encoding="utf-8")
        for ignored in (
            "incoming_payroll/",
            "outputs/reviews/",
            "outputs/audit/",
            "outputs/agent/",
            "real_data/",
        ):
            if ignored not in gitignore_text:
                warnings.append(f".gitignore does not explicitly ignore {ignored}")

    return ValidationResult(not errors, errors, warnings)


def validate_review_outputs(
    output_dir: Path,
    prefix: str,
    policy_path: Path = DEFAULT_POLICY_PATH,
) -> ValidationResult:
    policy = load_runtime_policy(policy_path)
    errors: list[str] = []
    warnings: list[str] = []

    output_dir = output_dir.resolve()
    paths = {
        suffix: output_dir / f"{prefix}{suffix}"
        for suffix in policy.get("required_output_suffixes", [])
    }

    for suffix, path in paths.items():
        if not path.exists():
            errors.append(f"Expected output is missing: {path.name}")

    receipt_path = paths.get("_receipt.json")
    manifest_path = paths.get("_manifest.json")

    if receipt_path and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        validate_receipt_flags(receipt, policy, errors)
    else:
        receipt = {}

    if manifest_path and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_manifest(receipt, manifest, errors, warnings)

    return ValidationResult(not errors, errors, warnings)


def validate_receipt_flags(
    receipt: dict[str, Any],
    policy: dict[str, Any],
    errors: list[str],
) -> None:
    for field, expected in policy.get("required_receipt_flags", {}).items():
        if receipt.get(field) != expected:
            errors.append(f"Receipt field {field!r} expected {expected!r}.")

    if not receipt.get("review_pack"):
        errors.append("Receipt is missing review_pack.")

    if not receipt.get("recommended_next_action"):
        errors.append("Receipt is missing recommended_next_action.")


def validate_manifest(
    receipt: dict[str, Any],
    manifest: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    if manifest.get("agent_mode") != ACTIVE_AGENT_MODE:
        errors.append("Manifest must use read_only_review mode.")

    if receipt and manifest.get("review_id") != receipt.get("review_id"):
        errors.append("Manifest review_id does not match receipt review_id.")

    file_hashes = manifest.get("file_hashes") or {}

    for field in (
        "current_file_sha256",
        "previous_file_sha256",
        "review_workbook_sha256",
        "summary_json_sha256",
        "receipt_json_sha256",
    ):
        value = str(file_hashes.get(field, ""))

        if len(value) != 64:
            errors.append(f"Manifest hash is missing or invalid: {field}")

    if not manifest.get("thresholds"):
        warnings.append("Manifest does not include thresholds.")
