from __future__ import annotations

import sys


def warn(message: str) -> None:
    print(f"warn: {message}", file=sys.stderr)


def error(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)

