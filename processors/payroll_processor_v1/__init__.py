import argparse
import sys
from pathlib import Path


ROOT_DIR: Path = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from gui.theme import accent, important
from .extractor import extract_payroll
from .field_mapper import infer_field
from .models import FieldMatch, PayrollExtraction
from .schema import EXPORT_FIELDS, PAYROLL_SCHEMA
from .streamlit_app import default_output_name, render_streamlit_app
from .workbook import exported_rows, save_payroll_workbook, workbook_to_bytes


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(description="Process a payroll PDF into a reviewed Excel workbook.")
    parser.add_argument("pdf", type=Path, help="Input payroll PDF file")
    parser.add_argument("-o", "--out", type=Path, help="Output XLSX file")

    return parser


def run_cli(argv: list[str] | None = None) -> None:
    """Run the payroll processor from the command line."""
    args: argparse.Namespace = build_parser().parse_args(argv)

    if not args.pdf.exists():
        raise SystemExit(f"PDF file not found: {args.pdf}")

    print(f"{accent('Reading PDF:')} {args.pdf}")
    extraction: PayrollExtraction = extract_payroll(args.pdf)
    print(f"{accent('Rows found:')} {important(len(extraction.rows))}")
    print(f"{accent('Fields reviewed:')} {important(len(extraction.field_matches))}")

    output_path: Path = args.out or args.pdf.with_suffix(".xlsx")
    save_payroll_workbook(extraction, output_path)
    print(f"{important('Complete.')} Wrote {output_path}")


def main() -> None:
    """Run the command-line interface."""
    run_cli()


__all__ = [
    "EXPORT_FIELDS",
    "FieldMatch",
    "PAYROLL_SCHEMA",
    "PayrollExtraction",
    "default_output_name",
    "exported_rows",
    "extract_payroll",
    "infer_field",
    "render_streamlit_app",
    "run_cli",
    "save_payroll_workbook",
    "workbook_to_bytes",
]


if __name__ == "__main__":
    main()
