"""Row capping and keyset paging for result sets that can grow unbounded (telemetry, alarms,
tickets), always newest first.

Capping must never leave the caller silently confident about incomplete data: a capped
result says so explicitly and carries a cursor to fetch the next (older) page from. The
cursor is (sort key, id) rather than a bare timestamp, so rows sharing a timestamp (or a
ticket date) are neither repeated nor skipped between pages.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

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
