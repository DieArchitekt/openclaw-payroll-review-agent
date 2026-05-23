from typing import Any

import pandas as pd


def dataframe(data: Any) -> pd.DataFrame:
    """Return data as a pandas DataFrame."""
    if isinstance(data, pd.DataFrame):
        return data

    return pd.DataFrame(data or [])


def anomaly_counts(anomalies_df: pd.DataFrame) -> dict[str, int]:
    """Return anomaly counts by severity."""
    if (
        anomalies_df is None
        or anomalies_df.empty
        or "Severity" not in anomalies_df.columns
    ):
        return {"HIGH": 0, "MEDIUM": 0}

    counts = anomalies_df["Severity"].value_counts()
    return {"HIGH": int(counts.get("HIGH", 0)), "MEDIUM": int(counts.get("MEDIUM", 0))}


def control_summary_rows(anomalies_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return exception counts by control category and severity."""
    if anomalies_df is None or anomalies_df.empty:
        return [
            {"Control": "All controls", "HIGH": 0, "MEDIUM": 0, "LOW": 0, "Total": 0}
        ]

    grouped = (
        anomalies_df.groupby(["Category", "Severity"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"Category": "Control"})
    )

    for severity in ("HIGH", "MEDIUM", "LOW"):
        if severity not in grouped.columns:
            grouped[severity] = 0

    grouped["Total"] = grouped[["HIGH", "MEDIUM", "LOW"]].sum(axis=1)
    return grouped[["Control", "HIGH", "MEDIUM", "LOW", "Total"]].to_dict("records")


def summary_metrics(summary: dict, anomalies_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return summary rows with visual section breaks."""
    counts: dict[str, int] = anomaly_counts(anomalies_df)

    return [
        {"Metric": "Employee counts", "Value": ""},
        {
            "Metric": "current employee count",
            "Value": summary.get("current_employee_count", 0),
        },
        {
            "Metric": "previous employee count",
            "Value": summary.get("previous_employee_count", 0),
        },
        {"Metric": "new employee count", "Value": summary.get("new_employee_count", 0)},
        {
            "Metric": "missing employee count",
            "Value": summary.get("missing_employee_count", 0),
        },
        {"Metric": "Payroll totals", "Value": ""},
        {
            "Metric": "current total net pay",
            "Value": summary.get("current_total_net_pay", 0.0),
        },
        {
            "Metric": "previous total net pay",
            "Value": summary.get("previous_total_net_pay", 0.0),
        },
        {"Metric": "net pay change", "Value": summary.get("net_pay_change", 0.0)},
        {
            "Metric": "employer cost change",
            "Value": summary.get("employer_cost_change", 0.0),
        },
        {
            "Metric": "employer cost change %",
            "Value": summary.get("employer_cost_change_pct", 0.0),
        },
        {"Metric": "Anomalies", "Value": ""},
        {"Metric": "HIGH anomalies", "Value": counts["HIGH"]},
        {"Metric": "MEDIUM anomalies", "Value": counts["MEDIUM"]},
    ]


def approval_summary_metrics(approval_record) -> list[dict[str, Any]]:
    """Return approval status rows for the Summary sheet."""
    if approval_record is None:
        return []

    return [
        {"Metric": "Approval", "Value": ""},
        {"Metric": "approval status", "Value": approval_record.status},
        {"Metric": "review id", "Value": approval_record.review_id},
        {
            "Metric": "prepared at",
            "Value": display_timestamp(approval_record.prepared_at),
        },
    ]


def approval_rows(approval_record) -> list[dict[str, Any]]:
    """Return rows for the Approval workbook sheet."""
    if approval_record is None:
        return []

    return [
        {"Field": "Review ID", "Value": approval_record.review_id},
        {"Field": "Status", "Value": approval_record.status},
        {"Field": "Prepared by", "Value": approval_record.prepared_by},
        {
            "Field": "Prepared at",
            "Value": display_timestamp(approval_record.prepared_at),
        },
        {"Field": "Reviewed by", "Value": approval_record.reviewed_by},
        {
            "Field": "Reviewed at",
            "Value": display_timestamp(approval_record.reviewed_at),
        },
        {"Field": "Approved by", "Value": approval_record.approved_by},
        {
            "Field": "Approved at",
            "Value": display_timestamp(approval_record.approved_at),
        },
        {"Field": "Exported by", "Value": approval_record.exported_by},
        {
            "Field": "Exported at",
            "Value": display_timestamp(approval_record.exported_at),
        },
        {"Field": "Reviewer comments", "Value": approval_record.reviewer_comments},
        {"Field": "Approval comments", "Value": approval_record.approval_comments},
        {"Field": "Query notes", "Value": approval_record.query_notes},
        {"Field": "Rejection reason", "Value": approval_record.rejection_reason},
        {
            "Field": "Last updated at",
            "Value": display_timestamp(approval_record.last_updated_at),
        },
    ]


def display_timestamp(value: Any) -> str:
    """Return a workbook-friendly timestamp string."""
    return value.isoformat(timespec="seconds") if value else ""
