from processors.anomaly_detector_v1 import detect_anomalies
from processors.reconciliation_engine_v1 import reconcile_payroll


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
