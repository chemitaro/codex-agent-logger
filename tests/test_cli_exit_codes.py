from pathlib import Path

import pytest

from codex_logger.cli import main

_PAYLOAD_OK = (
    '{"type":"agent-turn-complete","thread-id":"t1","turn-id":"u1","cwd":"/tmp","last-assistant-message":"ok"}'
)


def test_cli_nonzero_when_raw_save_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _raise_save_error(*_args: object, **_kwargs: object) -> Path:
        raise OSError("disk full")

    monkeypatch.setattr("codex_logger.cli.log_store.save_raw_payload", _raise_save_error)

    exit_code = main(['{"type":"agent-turn-complete"}'])

    stderr = capsys.readouterr().err
    assert exit_code != 0
    assert "failed to save raw payload" in stderr.lower()


def test_cli_nonzero_when_summary_rebuild_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")

    monkeypatch.setattr(
        "codex_logger.cli.log_store.save_raw_payload",
        lambda *_args, **_kwargs: saved_path,
    )

    def _raise_rebuild_error(*_args: object, **_kwargs: object) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr("codex_logger.cli.summary.rebuild_summary", _raise_rebuild_error)

    exit_code = main(['{"type":"agent-turn-complete"}'])

    stderr = capsys.readouterr().err
    assert exit_code != 0
    assert "failed to rebuild summary" in stderr.lower()


def test_cli_zero_when_telegram_send_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")
    monkeypatch.setattr(
        "codex_logger.cli.log_store.save_raw_payload",
        lambda *_args, **_kwargs: saved_path,
    )
    monkeypatch.setattr(
        "codex_logger.cli.summary.rebuild_summary",
        lambda *_args, **_kwargs: Path("/tmp/workspace/.codex-log/summary.md"),
    )

    def _raise_send_error(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "codex_logger.cli.telegram.send_last_message_best_effort", _raise_send_error
    )

    exit_code = main(["--telegram", _PAYLOAD_OK])
    stderr = capsys.readouterr().err
    assert exit_code == 0
    assert "telegram delivery failed" in stderr.lower()


def test_cli_zero_when_telegram_prereq_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")
    monkeypatch.setattr(
        "codex_logger.cli.log_store.save_raw_payload",
        lambda *_args, **_kwargs: saved_path,
    )
    monkeypatch.setattr(
        "codex_logger.cli.summary.rebuild_summary",
        lambda *_args, **_kwargs: Path("/tmp/workspace/.codex-log/summary.md"),
    )

    def _env_should_not_be_called(_cwd: Path) -> dict[str, str]:
        raise AssertionError("dotenv should not be loaded when payload is missing required fields")

    monkeypatch.setattr("codex_logger.telegram.env.load_env_from_dotenv", _env_should_not_be_called)

    payload_missing_last = (
        '{"type":"agent-turn-complete","thread-id":"t1","turn-id":"u1","cwd":"/tmp"}'
    )
    exit_code = main(["--telegram", payload_missing_last])
    stderr = capsys.readouterr().err
    assert exit_code == 0
    assert "telegram delivery skipped" in stderr.lower()


def test_cli_nonzero_when_local_save_fails_with_telegram(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _raise_save_error(*_args: object, **_kwargs: object) -> Path:
        raise OSError("disk full")

    monkeypatch.setattr("codex_logger.cli.log_store.save_raw_payload", _raise_save_error)

    exit_code = main(["--telegram", _PAYLOAD_OK])
    stderr = capsys.readouterr().err

    assert exit_code != 0
    assert "failed to save raw payload" in stderr.lower()
