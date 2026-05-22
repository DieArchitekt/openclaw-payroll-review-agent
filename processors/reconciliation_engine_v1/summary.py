import pandas as pd

from .constants import EMPLOYER_COST_FIELDS
from .math_utils import percent_change


def build_summary(current_df: pd.DataFrame, previous_df: pd.DataFrame, reconciliation: pd.DataFrame) -> dict:
    """Return summary metrics for the payroll comparison."""
    current_total_net_pay: float = total(current_df, "NetPay")
    previous_total_net_pay: float = total(previous_df, "NetPay")
    current_total_employer_cost: float = employer_cost(current_df)
    previous_total_employer_cost: float = employer_cost(previous_df)

    return {
        "current_employee_count": int(len(current_df)),
        "previous_employee_count": int(len(previous_df)),
        "new_employee_count": int((reconciliation["Status"] == "New").sum()),
        "missing_employee_count": int((reconciliation["Status"] == "Missing").sum()),
        "current_total_net_pay": current_total_net_pay,
        "previous_total_net_pay": previous_total_net_pay,
        "net_pay_change": current_total_net_pay - previous_total_net_pay,
        "net_pay_change_pct": percent_change(current_total_net_pay, previous_total_net_pay),
        "current_total_employer_cost": current_total_employer_cost,
        "previous_total_employer_cost": previous_total_employer_cost,
        "employer_cost_change": current_total_employer_cost - previous_total_employer_cost,
        "employer_cost_change_pct": percent_change(current_total_employer_cost, previous_total_employer_cost),
    }


def total(df: pd.DataFrame, field: str) -> float:
    """Return the numeric total for a payroll field."""
    if df.empty or field not in df.columns:
        return 0.0

    return float(df[field].sum())


def employer_cost(df: pd.DataFrame) -> float:
    """Return total employer cost for a payroll DataFrame."""
    if df.empty:
        return 0.0

    return float(sum(total(df, field) for field in EMPLOYER_COST_FIELDS))
