from pathlib import Path

import pytest

from codex_logger.gitignore import ensure_codex_log_ignored


def test_ensure_creates_gitignore(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    gitignore = workspace / ".gitignore"
    assert not gitignore.exists()

    changed = ensure_codex_log_ignored(workspace)

    assert changed is True
    assert gitignore.read_text(encoding="utf-8") == ".codex-log/\n"


def test_ensure_appends_once(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    gitignore = workspace / ".gitignore"
    gitignore.write_text("dist/\n", encoding="utf-8")

    changed = ensure_codex_log_ignored(workspace)
    assert changed is True
    assert gitignore.read_text(encoding="utf-8") == "dist/\n.codex-log/\n"

    changed_again = ensure_codex_log_ignored(workspace)
    assert changed_again is False
    assert gitignore.read_text(encoding="utf-8") == "dist/\n.codex-log/\n"


@pytest.mark.parametrize(
    "content",
    [
        ".codex-log/\n",
        ".codex-log\n",
        "/.codex-log/\n",
        "/.codex-log\n",
        "  .codex-log/  \n",
        "  /.codex-log  \n",
        "dist/\n.codex-log/\n",
    ],
)
def test_ensure_noop_when_present(tmp_path: Path, content: str) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    gitignore = workspace / ".gitignore"
    gitignore.write_text(content, encoding="utf-8")

    changed = ensure_codex_log_ignored(workspace)

    assert changed is False
    assert gitignore.read_text(encoding="utf-8") == content


def test_ensure_appends_with_newline(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    gitignore = workspace / ".gitignore"
    gitignore.write_text("dist/", encoding="utf-8")

    changed = ensure_codex_log_ignored(workspace)

    assert changed is True
    assert gitignore.read_text(encoding="utf-8") == "dist/\n.codex-log/\n"


def test_ensure_ignores_comments(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    gitignore = workspace / ".gitignore"
    gitignore.write_text("# .codex-log/\n", encoding="utf-8")

    changed = ensure_codex_log_ignored(workspace)

    assert changed is True
    assert gitignore.read_text(encoding="utf-8") == "# .codex-log/\n.codex-log/\n"
