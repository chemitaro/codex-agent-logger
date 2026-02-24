import hashlib
from pathlib import Path

from codex_logger.telegram import topic_name


def test_topic_name_normal() -> None:
    name = topic_name(Path("/path/to/project"), "abc")
    assert name == "project (abc)"
    assert len(name.encode("utf-8")) <= 128


def test_topic_name_shortens_thread_id_when_too_long() -> None:
    thread_id = "x" * 200
    short = hashlib.sha256(thread_id.encode("utf-8")).hexdigest()[:8]

    name = topic_name(Path("/path/to/project"), thread_id)
    assert name == f"project ({short})"
    assert len(name.encode("utf-8")) <= 128


def test_topic_name_truncates_cwd_basename_when_still_too_long() -> None:
    thread_id = "abc"
    short = hashlib.sha256(thread_id.encode("utf-8")).hexdigest()[:8]
    long_prefix = "あ" * 200
    cwd = Path("/tmp") / long_prefix

    name = topic_name(cwd, thread_id)

    assert name.endswith(f" ({short})")
    assert len(name.encode("utf-8")) <= 128
