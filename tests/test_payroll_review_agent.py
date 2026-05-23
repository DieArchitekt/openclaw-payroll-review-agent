from io import BytesIO
from types import SimpleNamespace

from openpyxl import load_workbook

from processors.anomaly_detector_v1 import detect_anomalies
import pytest

from processors.approval_workflow_v1 import (
    STATUS_APPROVED,
    STATUS_EXPORTED,
    STATUS_PREPARED,
    STATUS_QUERIES_RAISED,
    STATUS_REJECTED,
    STATUS_REVIEWED,
    approve_review,
    create_approval_record,
    mark_exported,
    mark_reviewed,
    raise_queries,
    reject_review,
)
from processors.payroll_processor_v1.extractor import extract_payroll
from processors.payroll_processor_v1.models import PayrollExtraction
from processors.payroll_review_workflow import run_payroll_review
from processors.reconciliation_engine_v1 import reconcile_payroll
from processors.report_generator import generate_review_workbook


class UploadedPayrollFile:
    def __init__(self, name: str, payload: str) -> None:
        self.name = name
        self.payload = payload.encode("utf-8")

    def getvalue(self) -> bytes:
        return self.payload


def test_extract_payroll_from_csv_with_dynamic_headers(tmp_path):
    source = tmp_path / "current.csv"
    source.write_text(
        "Worker,Gross monthly,Tax deducted,National Insurance,Take home,Employer NI,Employers pension\n"
        "Ada Lovelace,3000,400,250,2350,300,150\n",
        encoding="utf-8",
    )

    extraction = extract_payroll(source)

    assert extraction.rows[0]["Employee"] == "Ada Lovelace"
    assert extraction.rows[0]["GrossPay"] == 3000.0
    assert extraction.rows[0]["PAYE"] == 400.0
    assert extraction.rows[0]["EmployeeNI"] == 250.0
    assert extraction.rows[0]["NetPay"] == 2350.0
    assert extraction.rows[0]["EmployerNI"] == 300.0
    assert extraction.rows[0]["EmployerPension"] == 150.0


def test_reconciliation_and_anomalies_flag_expected_rows():
    current_rows = [
        {
            "Employee": "Ada Lovelace",
            "GrossPay": 3600.0,
            "PAYE": 500.0,
            "NetPay": 2600.0,
            "EmployerNI": 320.0,
            "EmployerPension": 150.0,
        },
        {
            "Employee": "Grace Hopper",
            "GrossPay": 2500.0,
            "PAYE": 300.0,
            "NetPay": 2000.0,
            "EmployerNI": 250.0,
            "EmployerPension": 120.0,
        },
    ]
    previous_rows = [
        {
            "Employee": "Ada Lovelace",
            "GrossPay": 3000.0,
            "PAYE": 400.0,
            "NetPay": 2350.0,
            "EmployerNI": 300.0,
            "EmployerPension": 150.0,
        },
        {
            "Employee": "Alan Turing",
            "GrossPay": 2800.0,
            "PAYE": 350.0,
            "NetPay": 2200.0,
            "EmployerNI": 280.0,
            "EmployerPension": 130.0,
        },
    ]

    reconciliation_df, summary = reconcile_payroll(current_rows, previous_rows)
    anomalies_df = detect_anomalies(
        current_rows, reconciliation_df, summary, variance_threshold=10.0
    )

    assert set(reconciliation_df["Status"]) == {"Existing", "New", "Missing"}
    assert summary["new_employee_count"] == 1
    assert summary["missing_employee_count"] == 1
    assert "HIGH" in set(anomalies_df["Severity"])


def test_review_pack_contains_expected_sheets():
    current = PayrollExtraction(
        rows=[{"Employee": "Ada Lovelace", "GrossPay": 3000.0, "NetPay": 2350.0}]
    )
    previous = PayrollExtraction(
        rows=[{"Employee": "Ada Lovelace", "GrossPay": 2900.0, "NetPay": 2300.0}]
    )
    reconciliation_df, summary = reconcile_payroll(current.rows, previous.rows)
    anomalies_df = detect_anomalies(current.rows, reconciliation_df, summary)

    result = SimpleNamespace(
        current_extraction=current,
        previous_extraction=previous,
        reconciliation_df=reconciliation_df,
        anomalies_df=anomalies_df,
        summary=summary,
        approval_record=create_approval_record("preparer"),
    )

    payload = generate_review_workbook(result)
    workbook = load_workbook(BytesIO(payload))

    assert workbook.sheetnames == [
        "Current Payroll",
        "Previous Payroll",
        "Reconciliation",
        "Anomalies",
        "Summary",
        "Approval",
        "Current Field Recognition",
        "Previous Field Recognition",
    ]
    assert workbook["Reconciliation"].freeze_panes == "A2"
    assert workbook["Approval"]["A2"].value == "Review ID"
    assert workbook["Summary"]["A2"].value == "approval status"


def test_run_payroll_review_returns_complete_result():
    current = UploadedPayrollFile(
        "current.csv",
        "Employee,GrossPay,PAYE,NetPay,EmployerNI,EmployerPension\nAda Lovelace,3000,400,2350,300,150\n",
    )
    previous = UploadedPayrollFile(
        "previous.csv",
        "Employee,GrossPay,PAYE,NetPay,EmployerNI,EmployerPension\nAda Lovelace,2900,390,2300,290,145\n",
    )

    result = run_payroll_review(
        current, previous, variance_threshold=20.0, prepared_by="Payroll preparer"
    )

    assert result.current_extraction.rows
    assert result.previous_extraction.rows
    assert not result.reconciliation_df.empty
    assert isinstance(result.summary, dict)
    assert result.approval_record.status == STATUS_PREPARED
    assert result.approval_record.prepared_by == "Payroll preparer"
    assert result.approval_record.review_id
    assert result.review_workbook_bytes.startswith(b"PK")


def test_approval_transitions_allow_expected_flow():
    record = create_approval_record("preparer")

    mark_reviewed(record, "reviewer", "looks fine")
    assert record.status == STATUS_REVIEWED
    assert record.reviewed_by == "reviewer"
    assert record.reviewer_comments == "looks fine"

    approve_review(record, "approver", "approved")
    assert record.status == STATUS_APPROVED
    assert record.approved_by == "approver"
    assert record.approval_comments == "approved"

    mark_exported(record, "exporter")
    assert record.status == STATUS_EXPORTED
    assert record.exported_by == "exporter"


def test_approval_queries_can_return_to_reviewed():
    record = create_approval_record("preparer")

    raise_queries(record, "reviewer", "missing explanation")
    assert record.status == STATUS_QUERIES_RAISED
    assert record.query_notes == "missing explanation"

    mark_reviewed(record, "reviewer", "query resolved")
    assert record.status == STATUS_REVIEWED
    assert record.reviewer_comments == "query resolved"


def test_approval_invalid_transitions_are_blocked():
    prepared = create_approval_record("preparer")

    with pytest.raises(ValueError):
        approve_review(prepared, "approver")

    rejected = create_approval_record("preparer")
    mark_reviewed(rejected, "reviewer")
    reject_review(rejected, "approver", "not acceptable")
    assert rejected.status == STATUS_REJECTED

    with pytest.raises(ValueError):
        mark_exported(rejected, "exporter")
