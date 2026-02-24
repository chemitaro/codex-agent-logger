from pathlib import Path

import pytest

from codex_logger.cli import main, parse_args


def test_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0


def test_version_exits_zero_without_payload() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0


def test_telegram_and_version_exits_zero_without_payload() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--telegram", "--version"])
    assert excinfo.value.code == 0


def test_normal_run_without_payload_is_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code != 0

    stderr = capsys.readouterr().err
    assert "usage:" in stderr


@pytest.mark.parametrize(
    "argv",
    [
        ['{"type":"agent-turn-complete"}'],
        ["--telegram", '{"type":"agent-turn-complete"}'],
    ],
)
def test_payload_json_with_or_without_telegram(
    argv: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    saved_path = Path("/tmp/workspace/.codex-log/logs/raw-payload.json")
    monkeypatch.setattr(
        "codex_logger.cli.log_store.save_raw_payload",
        lambda *_args, **_kwargs: saved_path,
    )
    rebuilt: list[Path] = []
    monkeypatch.setattr(
        "codex_logger.cli.summary.rebuild_summary",
        lambda base_dir: rebuilt.append(base_dir),
    )

    args = parse_args(argv)
    assert args.payload_json == '{"type":"agent-turn-complete"}'
    assert args.telegram == ("--telegram" in argv)

    assert main(argv) == 0
    assert rebuilt == [saved_path.parent.parent]


@pytest.mark.parametrize(
    "argv",
    [
        ["--unknown"],
        ['{"type":"agent-turn-complete"}', "extra"],
    ],
)
def test_unknown_or_extra_args_are_usage_error(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    assert excinfo.value.code != 0

    stderr = capsys.readouterr().err
    assert "usage:" in stderr

