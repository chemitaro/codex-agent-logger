import os
from pathlib import Path
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve(strict=False).parents[1]


def test_dev_runner_help() -> None:
    script = _repo_root() / "scripts" / "codex-logger-dev"
    assert script.exists()
    assert os.access(script, os.X_OK)

    proc = subprocess.run(
        [str(script), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0


def test_dev_runner_passes_payload(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    payload = (
        '{"type":"agent-turn-complete","thread-id":"t1","turn-id":"u1","cwd":"'
        + str(workspace)
        + '","last-assistant-message":"ok"}'
    )

    script = _repo_root() / "scripts" / "codex-logger-dev"
    env = os.environ.copy()
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)

    proc = subprocess.run(
        [str(script), "--telegram", payload],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0

    logs_dir = workspace.resolve(strict=False) / ".codex-log" / "logs"
    assert logs_dir.is_dir()
    assert list(logs_dir.glob("*.json"))

