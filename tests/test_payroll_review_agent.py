from io import BytesIO
from types import SimpleNamespace

from openpyxl import load_workbook

from processors.anomaly_detector_v1 import detect_anomalies
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
    )

    payload = generate_review_workbook(result)
    workbook = load_workbook(BytesIO(payload))

    assert workbook.sheetnames == [
        "Current Payroll",
        "Previous Payroll",
        "Reconciliation",
        "Anomalies",
        "Summary",
        "Current Field Recognition",
        "Previous Field Recognition",
    ]
    assert workbook["Reconciliation"].freeze_panes == "A2"


def test_run_payroll_review_returns_complete_result():
    current = UploadedPayrollFile(
        "current.csv",
        "Employee,GrossPay,PAYE,NetPay,EmployerNI,EmployerPension\nAda Lovelace,3000,400,2350,300,150\n",
    )
    previous = UploadedPayrollFile(
        "previous.csv",
        "Employee,GrossPay,PAYE,NetPay,EmployerNI,EmployerPension\nAda Lovelace,2900,390,2300,290,145\n",
    )

    result = run_payroll_review(current, previous, variance_threshold=20.0)

    assert result.current_extraction.rows
    assert result.previous_extraction.rows
    assert not result.reconciliation_df.empty
    assert isinstance(result.summary, dict)
    assert result.review_workbook_bytes.startswith(b"PK")
