from __future__ import annotations

import hashlib

MISSING_THREAD_ID = "<missing-thread-id>"
MISSING_TURN_ID = "<missing-turn-id>"


def event_id(thread_id: str | None, turn_id: str | None) -> str:
    safe_thread_id = thread_id if thread_id else MISSING_THREAD_ID
    safe_turn_id = turn_id if turn_id else MISSING_TURN_ID
    event_key = f"{safe_thread_id}:{safe_turn_id}"
    digest = hashlib.sha256(event_key.encode("utf-8")).hexdigest()[:12]
    return f"ev-{digest}"

