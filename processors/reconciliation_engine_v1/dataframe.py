from typing import Any

import pandas as pd

from .constants import RECONCILIATION_FIELDS
from .names import normalise_employee_name
from processors.payroll_processor_v1.schema import field_kind


def rows_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    """Return payroll rows as a normalised pandas DataFrame."""
    df: pd.DataFrame = pd.DataFrame(rows or [])
    df = with_expected_columns(df)
    df["Employee"] = df["Employee"].fillna("").astype(str)
    df["_employee_key"] = df["Employee"].map(normalise_employee_name)

    for field in numeric_fields():
        df[field] = pd.to_numeric(df[field], errors="coerce").fillna(0.0)

    return collapse_duplicate_employees(df)


def with_expected_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame containing every reconciliation field."""
    for field in RECONCILIATION_FIELDS:
        if field not in df.columns:
            df[field] = default_value(field)

    return df[RECONCILIATION_FIELDS].copy()


def numeric_fields() -> list[str]:
    """Return canonical payroll fields treated as numbers by reconciliation."""
    return [
        field
        for field in RECONCILIATION_FIELDS
        if field != "Employee" and field_kind(field) in {"money", "number"}
    ]


def text_fields() -> list[str]:
    """Return canonical payroll fields treated as text by reconciliation."""
    return [
        field
        for field in RECONCILIATION_FIELDS
        if field != "Employee" and field_kind(field) not in {"money", "number"}
    ]


def default_value(field: str) -> str | float:
    """Return a default value for one reconciliation field."""
    if field == "Employee" or field_kind(field) not in {"money", "number"}:
        return ""

    return 0.0


def collapse_duplicate_employees(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per normalised employee key."""
    if df.empty:
        return df

    named_rows: pd.DataFrame = df[df["_employee_key"] != ""].copy()

    if named_rows.empty:
        return empty_payroll_dataframe()

    aggregations: dict[str, Any] = {"Employee": "first"}
    aggregations.update({field: "sum" for field in numeric_fields()})
    aggregations.update({field: "first" for field in text_fields()})

    return named_rows.groupby("_employee_key", as_index=False).agg(aggregations)


def empty_payroll_dataframe() -> pd.DataFrame:
    """Return an empty payroll DataFrame with expected columns."""
    return pd.DataFrame(columns=RECONCILIATION_FIELDS + ["_employee_key"])
