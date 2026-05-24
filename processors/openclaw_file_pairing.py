import re
import time
from dataclasses import dataclass
from pathlib import Path

CURRENT_DIR = "current"
PREVIOUS_DIR = "previous"
CURRENT_MARKER = "_current"
PREVIOUS_MARKER = "_previous"
SUPPORTED_EXTENSIONS = {".pdf", ".csv", ".txt", ".xlsx", ".xlsm"}
PERIOD_SUFFIX_PATTERN = re.compile(r"([_-]\d{4}-\d{2})$")


@dataclass(frozen=True, slots=True)
class PayrollFilePair:
    """Store one current/previous payroll file pair found in the incoming folder."""

    key: str
    current_path: Path
    previous_path: Path


def find_payroll_pair(incoming_root: Path) -> PayrollFilePair:
    """Return the single discoverable payroll file pair for an incoming folder."""
    pairs = discover_payroll_pairs(incoming_root)

    if not pairs:
        raise FileNotFoundError(
            f"No payroll file pair found under {incoming_root}. "
            "Expected files in current/ and previous/ using _current and _previous markers."
        )

    if len(pairs) > 1:
        keys = ", ".join(pair.key for pair in pairs)
        raise ValueError(
            f"Multiple payroll file pairs found: {keys}. Specify files explicitly."
        )

    return pairs[0]


def wait_for_stable_payroll_pair(
    incoming_root: Path,
    timeout_seconds: float = 60.0,
    poll_interval_seconds: float = 2.0,
    stable_checks: int = 2,
) -> PayrollFilePair:
    """Wait for one discoverable payroll pair whose file sizes have stopped changing."""
    deadline = time.monotonic() + timeout_seconds
    last_signature: tuple[tuple[str, int, int], tuple[str, int, int]] | None = None
    stable_count = 0
    last_error: Exception | None = None

    while time.monotonic() <= deadline:
        try:
            pair = find_payroll_pair(incoming_root)
            signature = pair_signature(pair)

            if signature == last_signature:
                stable_count += 1
            else:
                stable_count = 1
                last_signature = signature

            if stable_count >= stable_checks:
                return pair
        except (FileNotFoundError, ValueError) as exc:
            last_error = exc
            stable_count = 0
            last_signature = None

        time.sleep(poll_interval_seconds)

    if last_error:
        raise TimeoutError(
            f"Timed out waiting for stable payroll pair: {last_error}"
        ) from last_error

    raise TimeoutError(
        f"Timed out waiting for stable payroll pair under {incoming_root}."
    )


def discover_payroll_pairs(incoming_root: Path) -> list[PayrollFilePair]:
    """Return matching current/previous files using the OpenClaw folder convention."""
    current_files = indexed_files(incoming_root / CURRENT_DIR, CURRENT_MARKER)
    previous_files = indexed_files(incoming_root / PREVIOUS_DIR, PREVIOUS_MARKER)
    keys = sorted(set(current_files).intersection(previous_files))

    return [
        PayrollFilePair(
            key=key,
            current_path=current_files[key],
            previous_path=previous_files[key],
        )
        for key in keys
    ]


def indexed_files(folder: Path, marker: str) -> dict[str, Path]:
    """Return supported files in a folder keyed by their payroll pairing key."""
    if not folder.exists():
        return {}

    files: dict[str, Path] = {}

    for path in sorted(folder.iterdir()):
        if not is_supported_payroll_file(path) or marker not in path.stem.lower():
            continue

        key = pairing_key(path, marker)
        if key and key not in files:
            files[key] = path

    return files


def pairing_key(path: Path, marker: str) -> str:
    """Return the stable client/file prefix used to pair current and previous files."""
    stem = path.stem.lower()
    prefix = stem.split(marker, 1)[0].strip("_- ")
    prefix = PERIOD_SUFFIX_PATTERN.sub("", prefix).strip("_- ")
    return prefix


def is_supported_payroll_file(path: Path) -> bool:
    """Return whether the path is a supported payroll input file."""
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def pair_signature(
    pair: PayrollFilePair,
) -> tuple[tuple[str, int, int], tuple[str, int, int]]:
    """Return file signatures used to decide whether a pair is stable."""
    return file_signature(pair.current_path), file_signature(pair.previous_path)


def file_signature(path: Path) -> tuple[str, int, int]:
    """Return a compact file stability signature."""
    stat = path.stat()
    return str(path), stat.st_size, stat.st_mtime_ns
