from typing import Any

import pandas as pd

from .constants import (
    BACS_TOLERANCE,
    HIGH_NET_PAY_THRESHOLD,
    LOW_NI_TO_GROSS_RATIO,
    LOW_PAYE_TO_GROSS_RATIO,
)
from .rules import (
    bacs_total_anomalies,
    duplicate_bank_account_anomalies,
    duplicate_employee_anomalies,
    duplicate_ni_number_anomalies,
    gross_pay_zero_tax_ni_anomalies,
    high_net_pay_anomalies,
    leaver_still_paid_anomalies,
    low_tax_ratio_anomalies,
    missing_department_cost_centre_anomalies,
    missing_pension_anomalies,
    negative_value_anomalies,
    negative_net_pay_anomalies,
    similar_name_duplicate_anomalies,
    starter_without_approval_anomalies,
    status_anomalies,
    summary_anomalies,
    variance_anomalies,
    zero_net_pay_anomalies,
)
from .utils import anomalies_dataframe


def detect_anomalies(
    current_rows,
    reconciliation_df: pd.DataFrame,
    summary: dict,
    variance_threshold: float = 20.0,
    high_net_pay_threshold: float = HIGH_NET_PAY_THRESHOLD,
    low_paye_ratio: float = LOW_PAYE_TO_GROSS_RATIO,
    low_ni_ratio: float = LOW_NI_TO_GROSS_RATIO,
    bacs_tolerance: float = BACS_TOLERANCE,
) -> pd.DataFrame:
    """Return payroll review anomalies from current rows, reconciliation, and summary."""
    anomalies: list[dict[str, Any]] = []

    anomalies.extend(duplicate_employee_anomalies(current_rows))
    anomalies.extend(duplicate_bank_account_anomalies(current_rows))
    anomalies.extend(duplicate_ni_number_anomalies(current_rows))
    anomalies.extend(similar_name_duplicate_anomalies(current_rows))
    anomalies.extend(status_anomalies(reconciliation_df))
    anomalies.extend(variance_anomalies(reconciliation_df, variance_threshold))
    anomalies.extend(leaver_still_paid_anomalies(current_rows))
    anomalies.extend(starter_without_approval_anomalies(current_rows))
    anomalies.extend(high_net_pay_anomalies(current_rows, high_net_pay_threshold))
    anomalies.extend(gross_pay_zero_tax_ni_anomalies(current_rows))
    anomalies.extend(missing_pension_anomalies(current_rows))
    anomalies.extend(
        low_tax_ratio_anomalies(current_rows, low_paye_ratio, low_ni_ratio)
    )
    anomalies.extend(missing_department_cost_centre_anomalies(current_rows))
    anomalies.extend(negative_net_pay_anomalies(current_rows))
    anomalies.extend(zero_net_pay_anomalies(current_rows))
    anomalies.extend(negative_value_anomalies(current_rows))
    anomalies.extend(bacs_total_anomalies(current_rows, summary, bacs_tolerance))
    anomalies.extend(summary_anomalies(summary, variance_threshold))

    return anomalies_dataframe(anomalies)
