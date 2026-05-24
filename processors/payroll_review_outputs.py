import json
from pathlib import Path
from typing import Any


def write_review_pack(output_path: Path, workbook_bytes: bytes) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(workbook_bytes)


def write_json(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
