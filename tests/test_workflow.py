from processors.approval_workflow_v1 import STATUS_PREPARED
from processors.payroll_review_workflow import run_payroll_review


class UploadedPayrollFile:
    def __init__(self, name: str, payload: str) -> None:
        self.name = name
        self.payload = payload.encode("utf-8")

    def getvalue(self) -> bytes:
        return self.payload


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
    assert result.thresholds["variance_threshold"] == 20.0
    assert result.agent_activity[0]["Action"] == "run_payroll_review"
    assert result.review_workbook_bytes.startswith(b"PK")
