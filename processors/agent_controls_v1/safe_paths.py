from pathlib import Path

DEFAULT_ALLOWED_WRITE_ROOTS = (Path("outputs"),)


def resolve_agent_path(
    path: str | Path,
    *,
    repo_root: Path | None = None,
    allowed_roots: tuple[Path, ...] = DEFAULT_ALLOWED_WRITE_ROOTS,
    allow_absolute: bool = False,
) -> Path:
    repo_root = (repo_root or Path.cwd()).resolve()
    supplied_path = Path(path)

    if supplied_path.is_absolute() and not allow_absolute:
        raise ValueError("Agent-supplied absolute paths are not allowed.")

    resolved = (
        supplied_path if supplied_path.is_absolute() else repo_root / supplied_path
    ).resolve()

    if not is_within(resolved, repo_root):
        raise ValueError("Agent path escapes the repository root.")

    allowed = tuple((repo_root / root).resolve() for root in allowed_roots)

    if not any(is_within(resolved, root) for root in allowed):
        allowed_text = ", ".join(str(root.relative_to(repo_root)) for root in allowed)
        raise ValueError(f"Agent path must stay under: {allowed_text}.")

    return resolved


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False

    return True
