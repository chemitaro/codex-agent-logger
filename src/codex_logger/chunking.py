from __future__ import annotations


def split_for_telegram(text: str, limit: int = 4096) -> list[str]:
    if limit <= 0:
        raise ValueError("limit must be > 0")
    if text == "":
        return ["(1/1)\n"]

    chunk_count_guess = 1
    while True:
        max_prefix_len = len(_prefix(chunk_count_guess, chunk_count_guess))
        body_limit = limit - max_prefix_len
        if body_limit <= 0:
            raise ValueError("limit is too small for chunk prefix")

        bodies = _split_body(text, body_limit)
        if len(bodies) == chunk_count_guess:
            break
        chunk_count_guess = len(bodies)

    chunk_count = len(bodies)
    return [_prefix(i + 1, chunk_count) + bodies[i] for i in range(chunk_count)]


def _prefix(i: int, n: int) -> str:
    return f"({i}/{n})\n"


def _split_body(text: str, limit: int) -> list[str]:
    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    current = ""

    for line in lines:
        if len(line) <= limit:
            if len(current) + len(line) <= limit:
                current += line
                continue

            if current:
                chunks.append(current)
            current = line
            continue

        if current:
            chunks.append(current)
            current = ""

        start = 0
        while start < len(line):
            chunks.append(line[start : start + limit])
            start += limit

    if current:
        chunks.append(current)

    return chunks or [""]

