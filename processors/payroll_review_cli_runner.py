import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from processors.agent_controls_v1.receipt import build_agent_receipt
from processors.cli_paths import resolve_manifest_path, resolve_output_paths
from processors.file_hashes import sha256_bytes, sha256_file
from processors.openclaw_file_pairing import (
    SUPPORTED_EXTENSIONS,
    find_payroll_pair,
    wait_for_stable_payroll_pair,
)
from processors.openclaw_reporting import review_completion_message
from processors.payroll_review_cli_args import build_parser
from processors.payroll_review_outputs import write_json, write_review_pack
from processors.payroll_review_summary import review_summary_payload
from processors.payroll_review_workflow import run_payroll_review
from processors.run_manifest_v1 import build_run_manifest


@dataclass(slots=True)
class LocalPayrollFile:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    def getvalue(self) -> bytes:
        return self.path.read_bytes()


def run_cli(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    current_path, previous_path = input_paths(args)
    output_path, summary_json_path, receipt_json_path = resolve_output_paths(
        args,
        current_path,
    )
    manifest_json_path = resolve_manifest_path(args, output_path)

    current_hash = sha256_file(current_path)
    previous_hash = sha256_file(previous_path)

    result = run_payroll_review(
        LocalPayrollFile(current_path),
        LocalPayrollFile(previous_path),
        variance_threshold=args.variance_threshold,
        prepared_by=args.prepared_by,
    )
    write_review_pack(output_path, result.review_workbook_bytes)
    workbook_hash = sha256_bytes(result.review_workbook_bytes)
    receipt = build_agent_receipt(
        result,
        output_path,
        summary_json_path,
        current_file_hash=current_hash,
        previous_file_hash=previous_hash,
        workbook_hash=workbook_hash,
    )
    payload = review_summary_payload(
        result,
        current_path,
        previous_path,
        output_path,
        summary_json_path,
        receipt_json_path,
        manifest_json_path,
        receipt,
    )

    if summary_json_path:
        write_json(summary_json_path, payload)
        receipt["file_hashes"]["summary_json_sha256"] = sha256_file(summary_json_path)

    if receipt_json_path:
        write_json(receipt_json_path, receipt)

    receipt_hash = sha256_file(receipt_json_path) if receipt_json_path else ""
    file_hashes = {
        **receipt["file_hashes"],
        "receipt_json_sha256": receipt_hash,
    }
    manifest = build_run_manifest(
        result,
        current_path=current_path,
        previous_path=previous_path,
        review_pack_path=output_path,
        summary_json_path=summary_json_path,
        receipt_json_path=receipt_json_path,
        manifest_json_path=manifest_json_path,
        file_hashes=file_hashes,
    )
    result.manifest = manifest
    write_json(manifest_json_path, manifest)

    if args.print_json:
        print(json.dumps(payload, indent=2))
    else:
        print(review_completion_message(payload))

    return 0


def input_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.incoming_root:
        try:
            if args.wait_for_pair:
                pair = wait_for_stable_payroll_pair(
                    args.incoming_root,
                    timeout_seconds=args.wait_timeout,
                    poll_interval_seconds=args.poll_interval,
                    stable_checks=args.stable_checks,
                )
            else:
                pair = find_payroll_pair(args.incoming_root)
        except (FileNotFoundError, TimeoutError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc

        return pair.current_path, pair.previous_path

    if not args.current or not args.previous:
        raise SystemExit("Provide current and previous files, or use --incoming-root.")

    validate_input_file(args.current, "Current payroll file")
    validate_input_file(args.previous, "Previous payroll file")
    return args.current, args.previous


def validate_input_file(path: Path, label: str) -> None:
    if not path.exists() or not path.is_file():
        raise SystemExit(f"{label} not found: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise SystemExit(
            f"{label} has unsupported file type: {path.suffix or 'unknown'}. "
            f"Supported types: {supported_file_types()}."
        )


def supported_file_types() -> str:
    return ", ".join(sorted(SUPPORTED_EXTENSIONS))


def cli_failure_message(reason: str) -> str:
    return "\n".join(
        [
            "Payroll review failed.",
            "",
            f"Reason: {reason}",
            "",
            "No files were moved, deleted, approved, rejected, exported, or sent.",
        ]
    )
