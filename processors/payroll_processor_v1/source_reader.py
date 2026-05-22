from pathlib import Path

import pandas as pd
import pdfplumber

from .models import RawPayrollSource


SPREADSHEET_SUFFIXES: set[str] = {".xlsx", ".xlsm"}
CSV_SUFFIXES: set[str] = {".csv", ".txt"}


def read_payroll_source(path: Path) -> RawPayrollSource:
    """Return raw tables and lines from a supported payroll source file."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return read_pdf_source(path)

    if suffix in CSV_SUFFIXES:
        return dataframe_source(pd.read_csv(path, header=None))

    if suffix in SPREADSHEET_SUFFIXES:
        return dataframe_source(pd.read_excel(path, header=None))

    raise ValueError(f"Unsupported payroll file type: {suffix or 'unknown'}")


def read_pdf_source(path: Path) -> RawPayrollSource:
    """Return raw tables and text extracted from a payroll file."""
    source = RawPayrollSource(tables=[])

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                source.raw_lines.extend(line for line in text.splitlines() if line.strip())

            source.tables.extend(page.extract_tables() or [])

    return source


def dataframe_source(df: pd.DataFrame) -> RawPayrollSource:
    """Return one raw table from a CSV or spreadsheet dataframe."""
    df = df.fillna("")
    rows: list[list[Any]] = df.astype(object).values.tolist()
    raw_lines: list[str] = [" ".join(str(value) for value in row if str(value).strip()) for row in rows]

    return RawPayrollSource(tables=[rows], raw_lines=[line for line in raw_lines if line])
