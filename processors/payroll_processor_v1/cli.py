import argparse
from pathlib import Path

from .extractor import extract_payroll
from .models import PayrollExtraction
from .workbook import save_payroll_workbook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process a payroll file into a payroll review output."
    )
    parser.add_argument("source", type=Path, help="Input payroll file")
    parser.add_argument("-o", "--out", type=Path, help="Output XLSX file")
    return parser


def run_cli(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if not args.source.exists():
        raise SystemExit(f"Payroll file not found: {args.source}")

    print(f"Reading payroll file: {args.source}")
    extraction: PayrollExtraction = extract_payroll(args.source)
    print(f"Rows found: {len(extraction.rows)}")
    print(f"Fields reviewed: {len(extraction.field_matches)}")

    output_path: Path = args.out or args.source.with_suffix(".xlsx")
    save_payroll_workbook(extraction, output_path)
    print(f"Complete. Wrote {output_path}")


def main() -> None:
    run_cli()
