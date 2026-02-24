import pytest

from codex_logger.cli import main


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
def test_payload_json_with_or_without_telegram(argv: list[str]) -> None:
    assert main(argv) == 0
