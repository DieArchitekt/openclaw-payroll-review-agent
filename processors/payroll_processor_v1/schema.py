from typing import Any


PAYROLL_SCHEMA: dict[str, dict[str, Any]] = {
    "Employee": {"label": "Employee", "aliases": ["employee", "employee name", "name", "worker", "staff", "staff member"], "kind": "text", "export": True},
    "EmployeeRef": {"label": "EmployeeRef", "aliases": ["ref", "reference", "employee ref", "employee number", "payroll id", "staff id"], "kind": "text", "export": False},
    "TaxCode": {"label": "TaxCode", "aliases": ["tax code", "taxcode", "code"], "kind": "text", "export": False},
    "NILetter": {"label": "NILetter", "aliases": ["ni letter", "ni category", "ni cat", "ni table", "category"], "kind": "text", "export": False},
    "GrossPay": {"label": "GrossPay", "aliases": ["gross", "gross pay", "gross monthly", "monthly gross", "salary", "basic pay"], "kind": "money", "export": True},
    "PreTaxAddDed": {"label": "PreTaxAddDed", "aliases": ["pre tax add ded", "pre tax add/ded", "pre tax adjustment", "pre tax additions"], "kind": "money", "export": False},
    "GUCosts": {"label": "GUCosts", "aliases": ["gu costs", "gu cost", "gu", "gu deduction"], "kind": "money", "export": False},
    "AbsencePay": {"label": "AbsencePay", "aliases": ["absence pay", "sick pay", "ssp", "statutory sick pay"], "kind": "money", "export": False},
    "HolidayPay": {"label": "HolidayPay", "aliases": ["holiday pay", "holiday", "annual leave pay"], "kind": "money", "export": False},
    "TaxablePay": {"label": "TaxablePay", "aliases": ["taxable pay", "taxable", "taxable gross"], "kind": "money", "export": False},
    "PreTaxPension": {"label": "PreTaxPension", "aliases": ["pre tax pension", "salary sacrifice pension", "pension pre tax"], "kind": "money", "export": True},
    "PAYE": {"label": "PAYE", "aliases": ["paye", "tax", "income tax", "tax deducted", "tax paid"], "kind": "money", "export": True},
    "EmployeeNI": {"label": "EmployeeNI", "aliases": ["employee ni", "ees ni", "ee ni", "employees ni", "net ni", "national insurance"], "kind": "money", "export": True},
    "PostTaxAddDed": {"label": "PostTaxAddDed", "aliases": ["post tax add ded", "post tax add/ded", "post tax adjustment"], "kind": "money", "export": False},
    "PostTaxPension": {"label": "PostTaxPension", "aliases": ["post tax pension", "pension post tax"], "kind": "money", "export": True},
    "AEO": {"label": "AEO", "aliases": ["aeo", "attachment of earnings", "earnings arrestment"], "kind": "money", "export": False},
    "StudentLoan": {"label": "StudentLoan", "aliases": ["student loan", "student loans", "sl deduction", "plan 1", "plan 2", "plan 4"], "kind": "money", "export": False},
    "PostgraduateLoan": {"label": "PostgraduateLoan", "aliases": ["postgraduate loan", "post graduate loan", "pgl"], "kind": "money", "export": False},
    "CourtOrder": {"label": "CourtOrder", "aliases": ["court order", "court deduction", "deduction from earnings order"], "kind": "money", "export": False},
    "UnionDeduction": {"label": "UnionDeduction", "aliases": ["union", "union deduction", "trade union"], "kind": "money", "export": False},
    "ChildcareVouchers": {"label": "ChildcareVouchers", "aliases": ["childcare", "childcare vouchers", "voucher"], "kind": "money", "export": False},
    "Benefits": {"label": "Benefits", "aliases": ["benefits", "bik", "benefit in kind", "benefits in kind"], "kind": "money", "export": False},
    "Expenses": {"label": "Expenses", "aliases": ["expenses", "expense", "reimbursement", "mileage"], "kind": "money", "export": False},
    "Bonus": {"label": "Bonus", "aliases": ["bonus", "bonuses"], "kind": "money", "export": False},
    "Commission": {"label": "Commission", "aliases": ["commission", "commissions"], "kind": "money", "export": False},
    "Overtime": {"label": "Overtime", "aliases": ["overtime", "ot", "overtime pay"], "kind": "money", "export": False},
    "Hours": {"label": "Hours", "aliases": ["hours", "hrs", "units", "quantity"], "kind": "number", "export": False},
    "Rate": {"label": "Rate", "aliases": ["rate", "hourly rate", "unit rate"], "kind": "number", "export": False},
    "NetPay": {"label": "NetPay", "aliases": ["net pay", "net", "take home", "take home pay", "paid", "amount paid"], "kind": "money", "export": True},
    "EmployerNI": {"label": "EmployerNI", "aliases": ["employer ni", "ers ni", "er ni", "employers ni", "net er ni", "class 1a"], "kind": "money", "export": True},
    "EmployerPension": {"label": "EmployerPension", "aliases": ["employer pension", "ers pension", "er pension", "employers pension"], "kind": "money", "export": True},
    "Department": {"label": "Department", "aliases": ["department", "dept", "team"], "kind": "text", "export": False},
    "CostCentre": {"label": "CostCentre", "aliases": ["cost centre", "cost center", "cost code", "division"], "kind": "text", "export": False},
    "PayPeriod": {"label": "PayPeriod", "aliases": ["pay period", "period", "payroll period"], "kind": "text", "export": False},
    "RunDate": {"label": "RunDate", "aliases": ["run date", "pay date", "payment date", "processed date"], "kind": "text", "export": False},
}

EXPORT_FIELDS: list[str] = [
    "Employee",
    "GrossPay",
    "PreTaxPension",
    "PAYE",
    "EmployeeNI",
    "PostTaxPension",
    "NetPay",
    "EmployerNI",
    "EmployerPension",
]

POSITIONAL_FALLBACK_FIELDS: list[str] = [
    "GrossPay",
    "GUCosts",
    "AbsencePay",
    "HolidayPay",
    "PreTaxPension",
    "TaxablePay",
    "PAYE",
    "EmployeeNI",
    "PostTaxAddDed",
    "PostTaxPension",
    "AEO",
    "StudentLoan",
    "NetPay",
    "EmployerNI",
    "EmployerPension",
]

HEADER_CONFIDENCE_THRESHOLD: float = 0.72


def field_kind(field_name: str) -> str:
    """Return the value type for a canonical field."""
    return PAYROLL_SCHEMA[field_name]["kind"]


def field_is_exported(field_name: str) -> bool:
    """Return whether a canonical field should appear in the main export."""
    return bool(PAYROLL_SCHEMA[field_name]["export"])


def output_header(field_name: str) -> str:
    """Return the export label for a canonical field."""
    return PAYROLL_SCHEMA[field_name]["label"]
