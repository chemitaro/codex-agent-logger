import re

from codex_logger.chunking import split_for_telegram


def test_single_chunk_adds_prefix() -> None:
    assert split_for_telegram("hello", limit=50) == ["(1/1)\nhello"]


def test_newline_preferred_split() -> None:
    text = "aaa\nbbb\nccc\n"
    chunks = split_for_telegram(text, limit=15)

    assert chunks == ["(1/2)\naaa\nbbb\n", "(2/2)\nccc\n"]


def test_force_split_long_line_when_needed() -> None:
    text = "abcdefghij"
    chunks = split_for_telegram(text, limit=10)

    assert len(chunks) == 3
    assert all(len(c) <= 10 for c in chunks)

    bodies = []
    for c in chunks:
        _prefix, body = c.split("\n", 1)
        bodies.append(body)
    assert "".join(bodies) == text


def test_prefix_included_in_limit_and_n_ge_10() -> None:
    text = "x" * 100
    chunks = split_for_telegram(text, limit=12)

    assert len(chunks) >= 10
    assert all(len(c) <= 12 for c in chunks)

    match0 = re.match(r"^\((\d+)/(\d+)\)\n", chunks[0])
    assert match0 is not None
    total = int(match0.group(2))
    assert total == len(chunks)

    for idx, chunk in enumerate(chunks, start=1):
        m = re.match(r"^\((\d+)/(\d+)\)\n", chunk)
        assert m is not None
        assert int(m.group(1)) == idx
        assert int(m.group(2)) == total
