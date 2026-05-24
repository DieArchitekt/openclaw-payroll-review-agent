import argparse
from pathlib import Path

from processors.cli_paths import DEFAULT_OUTPUT_DIR


def build_parser() -> argparse.ArgumentParser:
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
        "--agent-receipt-json",
        type=Path,
        help="Optional JSON receipt output path for automation agents",
    )
    parser.add_argument(
        "--manifest-json",
        type=Path,
        help="Optional JSON run manifest output path for audit evidence",
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
