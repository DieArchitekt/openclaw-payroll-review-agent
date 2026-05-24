from processors.payroll_processor_v1.extractor import extract_payroll


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
