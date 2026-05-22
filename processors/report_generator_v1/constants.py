from openpyxl.styles import Font, PatternFill


CURRENCY_FIELDS: tuple[str, ...] = (
    "GrossPay",
    "PreTaxPension",
    "PAYE",
    "EmployeeNI",
    "PostTaxPension",
    "NetPay",
    "EmployerNI",
    "EmployerPension",
    "Current Value",
    "Previous Value",
)

CURRENCY_CONTAINS: tuple[str, ...] = (
    "GrossPay",
    "NetPay",
    "PAYE",
    "EmployerNI",
    "EmployerPension",
    "net pay",
    "employer cost",
)

SHEET_NAMES: tuple[str, ...] = (
    "Current Payroll",
    "Previous Payroll",
    "Reconciliation",
    "Anomalies",
    "Summary",
    "Current Field Recognition",
    "Previous Field Recognition",
)

HEADER_FILL = PatternFill("solid", fgColor="111111")
HEADER_FONT = Font(bold=True, color="FFFFFF")
HIGH_FILL = PatternFill("solid", fgColor="F4CCCC")
MEDIUM_FILL = PatternFill("solid", fgColor="FCE5CD")
SECTION_FILL = PatternFill("solid", fgColor="D9EAD3")
SUMMARY_LABEL_FILL = PatternFill("solid", fgColor="EFEFEF")
