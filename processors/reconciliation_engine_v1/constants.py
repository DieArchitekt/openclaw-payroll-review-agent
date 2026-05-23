from processors.payroll_processor_v1.schema import EXPORT_FIELDS

CONTROL_FIELDS: list[str] = [
    "Bonus",
    "Overtime",
    "Commission",
    "EmployeeNI",
    "BankAccount",
    "SortCode",
    "NationalInsuranceNumber",
    "StarterFlag",
    "LeaverFlag",
    "StartDate",
    "LeaveDate",
    "StarterApproval",
    "LeaverApproval",
    "Department",
    "CostCentre",
    "BACSAmount",
]
RECONCILIATION_FIELDS: list[str] = list(dict.fromkeys(EXPORT_FIELDS + CONTROL_FIELDS))
COMPARE_FIELDS: list[str] = [
    "GrossPay",
    "NetPay",
    "PAYE",
    "EmployerNI",
    "EmployerPension",
    "EmployeeNI",
    "Bonus",
    "Overtime",
    "Commission",
]
EMPLOYER_COST_FIELDS: list[str] = ["GrossPay", "EmployerNI", "EmployerPension"]
