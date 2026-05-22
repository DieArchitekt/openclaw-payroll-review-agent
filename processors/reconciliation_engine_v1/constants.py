from processors.payroll_processor_v1.schema import EXPORT_FIELDS


RECONCILIATION_FIELDS: list[str] = list(EXPORT_FIELDS)
COMPARE_FIELDS: list[str] = ["GrossPay", "NetPay", "PAYE", "EmployerNI"]
EMPLOYER_COST_FIELDS: list[str] = ["GrossPay", "EmployerNI", "EmployerPension"]
