from pathlib import Path


def display_path(path: Path | None, repo_root: Path | None = None) -> str | None:
    if path is None:
        return None

    repo_root = repo_root or Path.cwd()
    resolved = path.resolve()

    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)
