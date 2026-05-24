import re
from typing import Any

import pandas as pd

BANK_ACCOUNT_FIELDS = {"BankAccount", "Bank Account", "AccountNumber"}
SORT_CODE_FIELDS = {"SortCode", "Sort Code"}
NI_FIELDS = {"NationalInsuranceNumber", "NI Number", "NINumber", "NI"}
SENSITIVE_FIELDS = BANK_ACCOUNT_FIELDS | SORT_CODE_FIELDS | NI_FIELDS

BANK_ACCOUNT_PATTERN = re.compile(r"\b\d{8}\b")
SORT_CODE_PATTERN = re.compile(r"\b\d{2}[- ]?\d{2}[- ]?\d{2}\b")
NI_PATTERN = re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}\s?\d{6}\s?[A-D]\b", re.IGNORECASE)


def mask_bank_account(value: Any) -> str:
    text = digits_only(value)

    if not text:
        return ""

    return f"****{text[-4:]}"


def mask_sort_code(value: Any) -> str:
    text = digits_only(value)

    if len(text) < 2:
        return "**-**-**" if text else ""

    return f"**-**-{text[-2:]}"


def mask_ni_number(value: Any) -> str:
    text = str(value or "").replace(" ", "").upper()

    if len(text) < 3:
        return "***" if text else ""

    return f"*****{text[-3:]}"


def redact_row(row: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(row)

    for field, value in row.items():
        if field in BANK_ACCOUNT_FIELDS:
            redacted[field] = mask_bank_account(value)
        elif field in SORT_CODE_FIELDS:
            redacted[field] = mask_sort_code(value)
        elif field in NI_FIELDS:
            redacted[field] = mask_ni_number(value)

    return redacted


def redact_anomalies_for_agent(anomalies_df: pd.DataFrame) -> list[dict[str, Any]]:
    if anomalies_df.empty:
        return []

    records: list[dict[str, Any]] = []

    for record in anomalies_df.to_dict(orient="records"):
        redacted = dict(record)
        field = str(record.get("Field", ""))

        if field in BANK_ACCOUNT_FIELDS:
            redacted["Current Value"] = mask_bank_account(record.get("Current Value"))
            redacted["Previous Value"] = mask_bank_account(record.get("Previous Value"))
        elif field in SORT_CODE_FIELDS:
            redacted["Current Value"] = mask_sort_code(record.get("Current Value"))
            redacted["Previous Value"] = mask_sort_code(record.get("Previous Value"))
        elif field in NI_FIELDS:
            redacted["Current Value"] = mask_ni_number(record.get("Current Value"))
            redacted["Previous Value"] = mask_ni_number(record.get("Previous Value"))

        redacted["Message"] = redact_text(record.get("Message", ""))
        records.append(redacted)

    return records


def redact_text(value: Any) -> str:
    text = str(value or "")
    text = BANK_ACCOUNT_PATTERN.sub(
        lambda match: mask_bank_account(match.group()), text
    )
    text = SORT_CODE_PATTERN.sub(lambda match: mask_sort_code(match.group()), text)
    text = NI_PATTERN.sub(lambda match: mask_ni_number(match.group()), text)
    return text


def digits_only(value: Any) -> str:
    return "".join(character for character in str(value or "") if character.isdigit())
