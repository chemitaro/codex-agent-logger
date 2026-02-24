from __future__ import annotations

import os
from pathlib import Path

from codex_logger.console import warn

_FILE_MODE = 0o600


def write_text_atomic(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    fd = os.open(tmp_path, flags, _FILE_MODE)
    try:
        with os.fdopen(fd, "wb") as file_obj:
            file_obj.write(content.encode("utf-8"))
            file_obj.flush()
            os.fsync(file_obj.fileno())
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError as exc:
            warn(f"failed to remove incomplete temp file {tmp_path}: {exc}")
        raise

    _try_chmod(tmp_path, _FILE_MODE)

    try:
        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError as exc:
            warn(f"failed to remove temp file {tmp_path}: {exc}")
        raise

    return path


def _try_chmod(path: Path, mode: int) -> None:
    try:
        os.chmod(path, mode)
    except OSError as exc:
        warn(f"failed to chmod {path}: {exc}")

