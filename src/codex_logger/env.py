from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values


def load_env_from_dotenv(cwd: Path) -> dict[str, str]:
    dotenv_path = cwd / ".env"
    if not dotenv_path.is_file():
        return {}

    values = dotenv_values(dotenv_path)
    return {k: v for k, v in values.items() if isinstance(k, str) and isinstance(v, str)}

