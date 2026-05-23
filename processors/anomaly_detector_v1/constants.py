from processors.payroll_processor_v1.schema import PAYROLL_SCHEMA

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

MONEY_FIELDS: list[str] = [
    field for field, config in PAYROLL_SCHEMA.items() if config["kind"] == "money"
]
VARIANCE_RULES: dict[str, str] = {
    "GrossPay": "HIGH",
    "NetPay": "HIGH",
    "PAYE": "MEDIUM",
    "EmployerNI": "MEDIUM",
    "EmployerPension": "MEDIUM",
    "EmployeeNI": "MEDIUM",
    "Bonus": "MEDIUM",
    "Overtime": "MEDIUM",
    "Commission": "MEDIUM",
}

HIGH_NET_PAY_THRESHOLD: float = 10000.0
LOW_PAYE_TO_GROSS_RATIO: float = 0.05
LOW_NI_TO_GROSS_RATIO: float = 0.02
BACS_TOLERANCE: float = 0.01
