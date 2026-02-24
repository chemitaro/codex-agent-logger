from pathlib import Path

import pytest

from codex_logger.gitignore import ensure_codex_log_dir_ignored


def test_ensure_creates_codex_log_gitignore(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    codex_log_dir = workspace / ".codex-log"
    gitignore = codex_log_dir / ".gitignore"
    assert not gitignore.exists()

    changed = ensure_codex_log_dir_ignored(codex_log_dir)

    assert changed is True
    assert gitignore.read_text(encoding="utf-8") == "*\n"


def test_ensure_overwrites_nonstandard_codex_log_gitignore(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    codex_log_dir = workspace / ".codex-log"
    codex_log_dir.mkdir()

    gitignore = codex_log_dir / ".gitignore"
    gitignore.write_text("dist/\n", encoding="utf-8")

    changed = ensure_codex_log_dir_ignored(codex_log_dir)

    assert changed is True
    assert gitignore.read_text(encoding="utf-8") == "*\n"

    changed_again = ensure_codex_log_dir_ignored(codex_log_dir)
    assert changed_again is False


def test_ensure_warns_on_codex_log_gitignore_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    codex_log_dir = workspace / ".codex-log"
    codex_log_dir.mkdir()
    (codex_log_dir / ".gitignore").mkdir()

    changed = ensure_codex_log_dir_ignored(codex_log_dir)

    assert changed is False
    stderr = capsys.readouterr().err
    assert "warn:" in stderr
    assert ".gitignore" in stderr
