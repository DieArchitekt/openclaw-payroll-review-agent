import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from processors.openclaw_file_pairing import (
    SUPPORTED_EXTENSIONS,
    find_payroll_pair,
    wait_for_stable_payroll_pair,
)
from processors.openclaw_reporting import review_completion_message
from processors.payroll_review_workflow import PayrollReviewResult, run_payroll_review

DEFAULT_OUTPUT_DIR = Path("outputs/reviews")
CURRENT_MARKER_PATTERN = re.compile(r"([_-])current$", re.IGNORECASE)
PERIOD_PATTERN = re.compile(r"\d{4}-\d{2}")
SAFE_PREFIX_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(slots=True)
class LocalPayrollFile:
    """Adapter that lets local files use the workflow upload protocol."""

    path: Path

    @property
    def name(self) -> str:
        """Return the source file name."""
        return self.path.name

    def getvalue(self) -> bytes:
        """Return local file contents as bytes."""
        return self.path.read_bytes()


def build_parser() -> argparse.ArgumentParser:
    """Return the payroll review CLI parser."""
    parser = argparse.ArgumentParser(
        description="Run a payroll review from current and previous payroll files."
    )
    parser.add_argument("current", nargs="?", type=Path, help="Current payroll file")
    parser.add_argument("previous", nargs="?", type=Path, help="Previous payroll file")
    parser.add_argument(
        "--incoming-root",
        type=Path,
        help="Incoming payroll folder containing current/ and previous/ subfolders",
    )
    parser.add_argument(
        "--wait-for-pair",
        action="store_true",
        help="Wait for a matching incoming payroll pair before running",
    )
    parser.add_argument(
        "--wait-timeout",
        type=float,
        default=60.0,
        help="Seconds to wait for incoming files when --wait-for-pair is used",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds between incoming folder checks when --wait-for-pair is used",
    )
    parser.add_argument(
        "--stable-checks",
        type=int,
        default=2,
        help="Matching file-size checks required before processing incoming files",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        help="Output review pack path. Overrides --output-dir naming.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Folder for generated review packs when --out is not supplied",
    )
    parser.add_argument(
        "--output-prefix",
        help="Optional output file prefix, for example client-a_2026-05",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        help="Optional JSON summary output path for automation",
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Print JSON summary to stdout",
    )
    parser.add_argument(
        "--variance-threshold",
        type=float,
        default=20.0,
        help="Percentage variance threshold for anomaly detection",
    )
    parser.add_argument(
        "--prepared-by",
        default="CLI",
        help="Name recorded as preparer in the approval record",
    )

    return parser


def run_cli(argv: list[str] | None = None) -> int:
    """Run the full payroll review from the command line."""
    args = build_parser().parse_args(argv)
    current_path, previous_path = input_paths(args)
    output_path, summary_json_path = resolve_output_paths(args, current_path)

    result = run_payroll_review(
        LocalPayrollFile(current_path),
        LocalPayrollFile(previous_path),
        variance_threshold=args.variance_threshold,
        prepared_by=args.prepared_by,
    )
    write_review_pack(output_path, result.review_workbook_bytes)
    payload = review_summary_payload(
        result,
        current_path,
        previous_path,
        output_path,
        summary_json_path,
    )

    if summary_json_path:
        write_json(summary_json_path, payload)

    if args.print_json:
        print(json.dumps(payload, indent=2))
    else:
        print(review_completion_message(payload))

    return 0


def input_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    """Return current and previous input paths from explicit files or an incoming folder."""
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
    """Raise a CLI-friendly error when an input file is missing."""
    if not path.exists() or not path.is_file():
        raise SystemExit(f"{label} not found: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise SystemExit(
            f"{label} has unsupported file type: {path.suffix or 'unknown'}. "
            f"Supported types: {supported_file_types()}."
        )


def supported_file_types() -> str:
    """Return supported payroll input extensions for CLI messages."""
    return ", ".join(sorted(SUPPORTED_EXTENSIONS))


def resolve_output_paths(
    args: argparse.Namespace,
    current_path: Path,
) -> tuple[Path, Path | None]:
    """Return workbook and summary paths without overwriting existing outputs."""
    if args.out:
        output_path = unused_path(args.out)
        summary_path = unused_path(args.summary_json) if args.summary_json else None
        return output_path, summary_path

    prefix = output_prefix(current_path, args.output_prefix)
    return unused_review_paths(args.output_dir, prefix)


def output_prefix(
    current_path: Path,
    explicit_prefix: str | None = None,
    timestamp: datetime | None = None,
) -> str:
    """Return a safe output prefix from an explicit value or current file name."""
    if explicit_prefix:
        return safe_output_prefix(explicit_prefix)

    stem = current_path.stem.strip()
    cleaned_stem = CURRENT_MARKER_PATTERN.sub("", stem).strip("_- ")

    if PERIOD_PATTERN.search(cleaned_stem):
        return safe_output_prefix(cleaned_stem)

    return safe_output_prefix(f"payroll_review_{timestamp_slug(timestamp)}")


def safe_output_prefix(value: str) -> str:
    """Return a filesystem-safe output prefix."""
    prefix = SAFE_PREFIX_PATTERN.sub("_", value.strip()).strip("._-")
    return prefix or f"payroll_review_{timestamp_slug()}"


def unused_review_paths(output_dir: Path, prefix: str) -> tuple[Path, Path]:
    """Return matching workbook and summary paths that do not overwrite files."""
    review_path = output_dir / f"{prefix}_review.xlsx"
    summary_path = output_dir / f"{prefix}_summary.json"

    if not review_path.exists() and not summary_path.exists():
        return review_path, summary_path

    base_prefix = f"{prefix}_{timestamp_slug()}"
    candidate_review = output_dir / f"{base_prefix}_review.xlsx"
    candidate_summary = output_dir / f"{base_prefix}_summary.json"
    counter = 2

    while candidate_review.exists() or candidate_summary.exists():
        candidate_review = output_dir / f"{base_prefix}_{counter}_review.xlsx"
        candidate_summary = output_dir / f"{base_prefix}_{counter}_summary.json"
        counter += 1

    return candidate_review, candidate_summary


def unused_path(path: Path) -> Path:
    """Return a path, adding a timestamp suffix if the requested path exists."""
    if not path.exists():
        return path

    stem = f"{path.stem}_{timestamp_slug()}"
    candidate = path.with_name(f"{stem}{path.suffix}")
    counter = 2

    while candidate.exists():
        candidate = path.with_name(f"{stem}_{counter}{path.suffix}")
        counter += 1

    return candidate


def timestamp_slug(timestamp: datetime | None = None) -> str:
    """Return a timestamp suitable for generated file names."""
    return (timestamp or datetime.now()).strftime("%Y-%m-%d_%H%M%S")


def write_review_pack(output_path: Path, workbook_bytes: bytes) -> None:
    """Write review workbook bytes to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(workbook_bytes)


def write_json(output_path: Path, payload: dict[str, Any]) -> None:
    """Write automation summary JSON to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def review_summary_payload(
    result: PayrollReviewResult,
    current_path: Path,
    previous_path: Path,
    output_path: Path,
    summary_json_path: Path | None = None,
) -> dict[str, Any]:
    """Return a redacted summary payload suitable for automation."""
    counts = anomaly_counts(result.anomalies_df)

    return {
        "review_id": result.approval_record.review_id,
        "approval_status": result.approval_record.status,
        "prepared_by": result.approval_record.prepared_by,
        "current_file": current_path.name,
        "previous_file": previous_path.name,
        "review_pack": str(output_path),
        "summary_json": str(summary_json_path) if summary_json_path else None,
        "variance_threshold": result.variance_threshold,
        "summary": result.summary,
        "high_exception_count": counts["HIGH"],
        "medium_exception_count": counts["MEDIUM"],
        "exception_count": int(len(result.anomalies_df)),
    }


def anomaly_counts(anomalies_df: pd.DataFrame) -> dict[str, int]:
    """Return anomaly counts by severity."""
    if anomalies_df.empty or "Severity" not in anomalies_df.columns:
        return {"HIGH": 0, "MEDIUM": 0}

    counts = anomalies_df["Severity"].value_counts()
    return {"HIGH": int(counts.get("HIGH", 0)), "MEDIUM": int(counts.get("MEDIUM", 0))}


def main() -> None:
    """Run the CLI entry point."""
    try:
        raise SystemExit(run_cli())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(cli_failure_message(exc.code), file=sys.stderr)
            raise SystemExit(1) from exc

        raise
    except Exception as exc:
        print(cli_failure_message(str(exc)), file=sys.stderr)
        raise SystemExit(1) from exc


def cli_failure_message(reason: str) -> str:
    """Return the short failure message an automation agent can read."""
    return "\n".join(
        [
            "Payroll review failed.",
            "",
            f"Reason: {reason}",
            "",
            "No files were moved, deleted, approved, rejected, exported, or sent.",
        ]
    )


if __name__ == "__main__":
    main()
