from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import os
from pathlib import Path

from codex_logger.console import warn
from codex_logger.ids import event_id
from codex_logger.timefmt import ts_utc_ms

_DIR_MODE = 0o700
_FILE_MODE = 0o600


def save_raw_payload(
    raw_payload: str,
    payload_cwd: str | None,
    thread_id: str | None,
    turn_id: str | None,
    now_utc: Callable[[], datetime] | None = None,
) -> Path:
    base_cwd = _resolve_base_cwd(payload_cwd)

    codex_log_dir = base_cwd / ".codex-log"
    logs_dir = codex_log_dir / "logs"

    _ensure_directory(codex_log_dir)
    _ensure_directory(logs_dir)

    current_utc = now_utc() if now_utc is not None else datetime.now(timezone.utc)
    timestamp = ts_utc_ms(current_utc)
    safe_event_id = event_id(thread_id, turn_id)

    raw_payload_bytes = raw_payload.encode("utf-8")
    return _write_payload_file(logs_dir, f"{timestamp}_{safe_event_id}", raw_payload_bytes)


def _resolve_base_cwd(payload_cwd: str | None) -> Path:
    if payload_cwd is not None:
        return Path(payload_cwd).resolve(strict=False)

    return Path.cwd().resolve(strict=False)


def _ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _try_chmod(path, _DIR_MODE)


def _try_chmod(path: Path, mode: int) -> None:
    try:
        os.chmod(path, mode)
    except OSError as exc:
        warn(f"failed to chmod {path}: {exc}")


def _write_payload_file(logs_dir: Path, stem: str, payload_bytes: bytes) -> Path:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    for attempt in range(1000):
        suffix = "" if attempt == 0 else f"__{attempt:02d}"
        candidate = logs_dir / f"{stem}{suffix}.json"

        try:
            fd = os.open(candidate, flags, _FILE_MODE)
        except FileExistsError:
            continue

        try:
            with os.fdopen(fd, "wb") as file_obj:
                file_obj.write(payload_bytes)
        except Exception:
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                candidate.unlink(missing_ok=True)
            except OSError as exc:
                warn(f"failed to remove incomplete log file {candidate}: {exc}")
            raise

        _try_chmod(candidate, _FILE_MODE)
        return candidate

    raise FileExistsError(f"too many collisions for {stem}.json")
