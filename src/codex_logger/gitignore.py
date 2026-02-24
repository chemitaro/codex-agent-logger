from __future__ import annotations

from pathlib import Path

from codex_logger.atomic import write_text_atomic
from codex_logger.console import warn

_CODEX_LOG_GITIGNORE_CONTENT = "*\n"


def ensure_codex_log_dir_ignored(codex_log_dir: Path) -> bool:
    codex_log_dir_gitignore = codex_log_dir / ".gitignore"

    try:
        if codex_log_dir.exists() and codex_log_dir.is_symlink():
            warn(f"skipping {codex_log_dir_gitignore} because {codex_log_dir} is a symlink")
            return False
    except OSError as exc:
        warn(f"failed to stat {codex_log_dir}: {exc}")
        return False

    try:
        if codex_log_dir_gitignore.exists() and codex_log_dir_gitignore.is_symlink():
            warn(
                f"skipping {codex_log_dir_gitignore} because it is a symlink"
            )
            return False
    except OSError as exc:
        warn(f"failed to stat {codex_log_dir_gitignore}: {exc}")
        return False

    existing: str | None
    try:
        existing = (
            codex_log_dir_gitignore.read_text(encoding="utf-8")
            if codex_log_dir_gitignore.exists()
            else None
        )
    except (OSError, UnicodeError):
        existing = None

    if existing == _CODEX_LOG_GITIGNORE_CONTENT:
        return False

    try:
        write_text_atomic(codex_log_dir_gitignore, _CODEX_LOG_GITIGNORE_CONTENT)
    except (OSError, UnicodeError) as exc:
        warn(f"failed to update {codex_log_dir_gitignore}: {exc}")
        return False

    return True
