"""Row capping and keyset paging for result sets that can grow unbounded (telemetry, alarms,
tickets), always newest first.

Capping must never leave the caller silently confident about incomplete data: a capped
result says so explicitly and carries a cursor to fetch the next (older) page from. The
cursor is (sort key, id) rather than a bare timestamp, so rows sharing a timestamp (or a
ticket date) are neither repeated nor skipped between pages.
"""

import base64
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Generic, TypeVar

from app.core.exceptions import InvalidCursorError

T = TypeVar("T")

MAX_ROWS = 100


@dataclass(frozen=True)
class Cursor:
    """Position of a row in a newest-first result: pass it as `before` to get strictly older rows."""

    sort_key: Any  # the row's timestamp / date
    id: str


@dataclass
class CappedResult(Generic[T]):
    rows: list[T]
    returned_count: int
    truncated: bool
    oldest_included_timestamp: Any
    next_cursor: Cursor | None  # set only when truncated


def clamp_limit(limit: int) -> int:
    """Callers may ask for fewer rows, never more than MAX_ROWS."""
    return max(1, min(limit, MAX_ROWS))


def cap_rows(rows: Sequence[T], max_rows: int, cursor_of: Callable[[T], Cursor]) -> CappedResult[T]:
    """Cap rows (fetched newest first with LIMIT max_rows + 1) to max_rows."""
    kept = list(rows[:max_rows])
    truncated = len(rows) > max_rows
    last = cursor_of(kept[-1]) if kept else None
    return CappedResult(
        rows=kept,
        returned_count=len(kept),
        truncated=truncated,
        oldest_included_timestamp=last.sort_key if last else None,
        next_cursor=last if truncated else None,
    )


def encode_cursor(cursor: Cursor | None) -> str | None:
    """Opaque URL-safe token for clients; decode_cursor is its inverse."""
    if cursor is None:
        return None
    kind = "datetime" if isinstance(cursor.sort_key, datetime) else "date"
    payload = json.dumps([kind, cursor.sort_key.isoformat(), cursor.id])
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(token: str | None) -> Cursor | None:
    if token is None:
        return None
    try:
        kind, iso, row_id = json.loads(base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)))
        sort_key = datetime.fromisoformat(iso) if kind == "datetime" else date.fromisoformat(iso)
        return Cursor(sort_key, str(row_id))
    except (ValueError, TypeError, KeyError):
        raise InvalidCursorError("Invalid pagination cursor.") from None
