import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from processors.openclaw_file_pairing import find_payroll_pair
from processors.payroll_review_workflow import PayrollReviewResult, run_payroll_review

DEFAULT_OUTPUT_PATH = Path("outputs/reviews/payroll_review.xlsx")


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
        "-o",
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output review pack path",
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

    result = run_payroll_review(
        LocalPayrollFile(current_path),
        LocalPayrollFile(previous_path),
        variance_threshold=args.variance_threshold,
        prepared_by=args.prepared_by,
    )
    write_review_pack(args.out, result.review_workbook_bytes)
    payload = review_summary_payload(result, current_path, previous_path, args.out)

    if args.summary_json:
        write_json(args.summary_json, payload)

    if args.print_json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Review pack written: {args.out}")
        print(f"Review ID: {payload['review_id']}")
        print(f"Approval status: {payload['approval_status']}")
        print(f"High exceptions: {payload['high_exception_count']}")
        print(f"Medium exceptions: {payload['medium_exception_count']}")

    return 0


def input_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    """Return current and previous input paths from explicit files or an incoming folder."""
    if args.incoming_root:
        try:
            pair = find_payroll_pair(args.incoming_root)
        except (FileNotFoundError, ValueError) as exc:
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
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
