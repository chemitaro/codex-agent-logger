from __future__ import annotations

from pathlib import Path

from codex_logger.atomic import write_text_atomic
from codex_logger.console import warn

_CODEX_LOG_RULE = ".codex-log/"
_EQUIVALENT_RULES = {
    ".codex-log",
    ".codex-log/",
    "/.codex-log",
    "/.codex-log/",
}


def ensure_codex_log_ignored(base_cwd: Path) -> bool:
    gitignore_path = base_cwd / ".gitignore"

    try:
        existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
    except (OSError, UnicodeError) as exc:
        warn(f"failed to read {gitignore_path}: {exc}")
        return False

    if _has_equivalent_rule(existing):
        return False

    updated = _append_rule(existing, _CODEX_LOG_RULE)
    try:
        write_text_atomic(gitignore_path, updated)
    except (OSError, UnicodeError) as exc:
        warn(f"failed to update {gitignore_path}: {exc}")
        return False

    return True


def _has_equivalent_rule(content: str) -> bool:
    for line in content.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        if normalized.startswith("#"):
            continue
        if normalized in _EQUIVALENT_RULES:
            return True
    return False


def _append_rule(content: str, rule: str) -> str:
    if not content:
        return f"{rule}\n"
    if content.endswith("\n"):
        return f"{content}{rule}\n"
    return f"{content}\n{rule}\n"
