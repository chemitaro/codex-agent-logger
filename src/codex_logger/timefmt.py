from __future__ import annotations

from datetime import datetime, timezone


def ts_utc_ms(now: datetime) -> str:
    if now.tzinfo is None:
        utc = now.replace(tzinfo=timezone.utc)
    else:
        utc = now.astimezone(timezone.utc)

    millis = utc.microsecond // 1000
    return utc.strftime("%Y-%m-%dT%H-%M-%S.") + f"{millis:03d}Z"

