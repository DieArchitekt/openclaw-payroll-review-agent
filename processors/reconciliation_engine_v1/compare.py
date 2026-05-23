import pandas as pd

from .constants import COMPARE_FIELDS
from .dataframe import numeric_fields, rows_to_dataframe
from .math_utils import percent_change
from .names import display_employee_name
from .summary import build_summary


def reconcile_payroll(current_rows, previous_rows) -> tuple[pd.DataFrame, dict]:
    """Compare current payroll rows against previous payroll rows."""
    current_df: pd.DataFrame = rows_to_dataframe(current_rows)
    previous_df: pd.DataFrame = rows_to_dataframe(previous_rows)
    reconciliation: pd.DataFrame = merged_reconciliation_frame(current_df, previous_df)
    summary: dict = build_summary(current_df, previous_df, reconciliation)

    return reconciliation, summary


def merged_reconciliation_frame(
    current_df: pd.DataFrame, previous_df: pd.DataFrame
) -> pd.DataFrame:
    """Return an outer-joined comparison DataFrame."""
    merged: pd.DataFrame = current_df.merge(
        previous_df,
        on="_employee_key",
        how="outer",
        suffixes=("_current", "_previous"),
        indicator=True,
    )

    merged["Employee"] = merged.apply(display_employee_name, axis=1)
    merged["Status"] = merged["_merge"].map(
        {"both": "Existing", "left_only": "New", "right_only": "Missing"}
    )
    fill_numeric_columns(merged)

    return build_reconciliation_columns(merged)


def fill_numeric_columns(merged: pd.DataFrame) -> None:
    """Fill missing current/previous numeric values after an outer join."""
    for field in numeric_fields():
        merged[f"{field}_current"] = merged[f"{field}_current"].fillna(0.0)
        merged[f"{field}_previous"] = merged[f"{field}_previous"].fillna(0.0)


def build_reconciliation_columns(merged: pd.DataFrame) -> pd.DataFrame:
    """Return the final reconciliation table with requested columns."""
    output: pd.DataFrame = merged[["Employee", "Status"]].copy()

    for field in COMPARE_FIELDS:
        add_comparison_columns(output, merged, field)

    return output[reconciliation_column_order()]


def add_comparison_columns(
    output: pd.DataFrame, merged: pd.DataFrame, field: str
) -> None:
    """Add current, previous, change, and change-percent columns for a field."""
    current_col: str = f"{field}_current"
    previous_col: str = f"{field}_previous"

    output[f"Current {field}"] = merged[current_col]
    output[f"Previous {field}"] = merged[previous_col]
    output[f"{field} Change"] = merged[current_col] - merged[previous_col]
    output[f"{field} Change %"] = percent_change(
        merged[current_col], merged[previous_col]
    )


def reconciliation_column_order() -> list[str]:
    """Return the exact output column order for reconciliation."""
    columns: list[str] = ["Employee", "Status"]

    for field in COMPARE_FIELDS:
        columns.extend(
            [
                f"Current {field}",
                f"Previous {field}",
                f"{field} Change",
                f"{field} Change %",
            ]
        )

    return columns
