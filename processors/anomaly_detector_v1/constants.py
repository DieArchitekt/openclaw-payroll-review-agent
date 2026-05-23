from processors.payroll_processor_v1.schema import EXPORT_FIELDS

ANOMALY_COLUMNS: list[str] = [
    "Severity",
    "Category",
    "Employee",
    "Field",
    "Current Value",
    "Previous Value",
    "Change %",
    "Message",
]

MONEY_FIELDS: list[str] = [field for field in EXPORT_FIELDS if field != "Employee"]
VARIANCE_RULES: dict[str, str] = {
    "GrossPay": "HIGH",
    "NetPay": "HIGH",
    "PAYE": "MEDIUM",
    "EmployerNI": "MEDIUM",
    "EmployerPension": "MEDIUM",
}
