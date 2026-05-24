import argparse
import re
from datetime import datetime
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("outputs/reviews")
CURRENT_MARKER_PATTERN = re.compile(r"([_-])current$", re.IGNORECASE)
PERIOD_PATTERN = re.compile(r"\d{4}-\d{2}")
SAFE_PREFIX_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def resolve_output_paths(
    args: argparse.Namespace,
    current_path: Path,
) -> tuple[Path, Path | None, Path | None]:
    if args.out:
        output_path = unused_path(args.out)
        summary_path = unused_path(args.summary_json) if args.summary_json else None
        receipt_path = (
            unused_path(args.agent_receipt_json) if args.agent_receipt_json else None
        )
        return output_path, summary_path, receipt_path

    prefix = output_prefix(current_path, args.output_prefix)
    return unused_review_paths(args.output_dir, prefix)


def resolve_manifest_path(args: argparse.Namespace, output_path: Path) -> Path:
    if getattr(args, "manifest_json", None):
        return unused_path(args.manifest_json)

    name = output_path.name

    if name.endswith("_review.xlsx"):
        return unused_path(
            output_path.with_name(name.replace("_review.xlsx", "_manifest.json"))
        )

    return unused_path(output_path.with_name(f"{output_path.stem}_manifest.json"))


def output_prefix(
    current_path: Path,
    explicit_prefix: str | None = None,
    timestamp: datetime | None = None,
) -> str:
    if explicit_prefix:
        return safe_output_prefix(explicit_prefix)

    stem = current_path.stem.strip()
    cleaned_stem = CURRENT_MARKER_PATTERN.sub("", stem).strip("_- ")

    if PERIOD_PATTERN.search(cleaned_stem):
        return safe_output_prefix(cleaned_stem)

    return safe_output_prefix(f"payroll_review_{timestamp_slug(timestamp)}")


def safe_output_prefix(value: str) -> str:
    prefix = SAFE_PREFIX_PATTERN.sub("_", value.strip()).strip("._-")
    return prefix or f"payroll_review_{timestamp_slug()}"


def unused_review_paths(output_dir: Path, prefix: str) -> tuple[Path, Path, Path]:
    review_path = output_dir / f"{prefix}_review.xlsx"
    summary_path = output_dir / f"{prefix}_summary.json"
    receipt_path = output_dir / f"{prefix}_receipt.json"

    if (
        not review_path.exists()
        and not summary_path.exists()
        and not receipt_path.exists()
    ):
        return review_path, summary_path, receipt_path

    base_prefix = f"{prefix}_{timestamp_slug()}"
    candidate_review = output_dir / f"{base_prefix}_review.xlsx"
    candidate_summary = output_dir / f"{base_prefix}_summary.json"
    candidate_receipt = output_dir / f"{base_prefix}_receipt.json"
    counter = 2

    while (
        candidate_review.exists()
        or candidate_summary.exists()
        or candidate_receipt.exists()
    ):
        candidate_review = output_dir / f"{base_prefix}_{counter}_review.xlsx"
        candidate_summary = output_dir / f"{base_prefix}_{counter}_summary.json"
        candidate_receipt = output_dir / f"{base_prefix}_{counter}_receipt.json"
        counter += 1

    return candidate_review, candidate_summary, candidate_receipt


def unused_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = f"{path.stem}_{timestamp_slug()}"
    candidate = path.with_name(f"{stem}{path.suffix}")
    counter = 2

    while candidate.exists():
        candidate = path.with_name(f"{stem}_{counter}{path.suffix}")
        counter += 1

    return candidate


def timestamp_slug(timestamp: datetime | None = None) -> str:
    return (timestamp or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
