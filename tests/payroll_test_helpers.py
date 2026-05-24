from pathlib import Path


def write_basic_payroll_pair(current: Path, previous: Path) -> None:
    current.write_text(
        "Employee,GrossPay,PAYE,EmployeeNI,NetPay,EmployerNI,EmployerPension\n"
        "Ada Lovelace,3000,400,250,2350,300,150\n",
        encoding="utf-8",
    )
    previous.write_text(
        "Employee,GrossPay,PAYE,EmployeeNI,NetPay,EmployerNI,EmployerPension\n"
        "Ada Lovelace,2900,390,240,2300,290,145\n",
        encoding="utf-8",
    )
