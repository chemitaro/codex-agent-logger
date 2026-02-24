from pathlib import Path

import pytest

from codex_logger.cli import main


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

