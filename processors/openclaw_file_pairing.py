import time
from dataclasses import dataclass
from pathlib import Path

CURRENT_STEM = "current"
PREVIOUS_STEM = "previous"
SUPPORTED_EXTENSIONS = {".pdf", ".csv", ".txt", ".xlsx", ".xlsm"}


@dataclass(frozen=True, slots=True)
class PayrollFilePair:
    """Store one current/previous payroll file pair found in the incoming folder."""

    key: str
    current_path: Path
    previous_path: Path


def find_payroll_pair(incoming_root: Path) -> PayrollFilePair:
    """Return the single current/previous payroll pair from a flat incoming folder."""
    pairs = discover_payroll_pairs(incoming_root)

    if not pairs:
        raise FileNotFoundError(
            f"No payroll file pair found under {incoming_root}. "
            "Expected current.<type> and previous.<type> in the incoming folder."
        )

    return pairs[0]


def wait_for_stable_payroll_pair(
    incoming_root: Path,
    timeout_seconds: float = 60.0,
    poll_interval_seconds: float = 2.0,
    stable_checks: int = 2,
) -> PayrollFilePair:
    """Wait for the incoming current/previous files to stop changing."""
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
    """Return the current/previous pair using the OpenClaw flat folder convention."""
    if not incoming_root.exists():
        return []

    supported_files = sorted(
        path for path in incoming_root.iterdir() if is_supported_payroll_file(path)
    )
    current_files = files_named(supported_files, CURRENT_STEM)
    previous_files = files_named(supported_files, PREVIOUS_STEM)
    unexpected_files = [
        path
        for path in supported_files
        if path.stem.lower() not in {CURRENT_STEM, PREVIOUS_STEM}
    ]

    if unexpected_files:
        names = ", ".join(path.name for path in unexpected_files)
        raise ValueError(f"Unexpected payroll files found in incoming folder: {names}.")

    if len(current_files) > 1 or len(previous_files) > 1:
        raise ValueError(
            "Incoming folder must contain one current file and one previous file."
        )

    if not current_files or not previous_files:
        return []

    return [
        PayrollFilePair(
            key="incoming_payroll",
            current_path=current_files[0],
            previous_path=previous_files[0],
        )
    ]


def files_named(paths: list[Path], stem: str) -> list[Path]:
    """Return supported files whose filename stem matches the requested role."""
    return [path for path in paths if path.stem.lower() == stem]


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
