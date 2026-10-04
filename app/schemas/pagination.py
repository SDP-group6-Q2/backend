from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.core.pagination import CappedResult, encode_cursor

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """A capped page, newest first unless stated otherwise. When `truncated`, pass `next_cursor`
    as the `cursor` query parameter to get the next (older) page."""

    rows: list[T]
    returned_count: int
    truncated: bool
    oldest_included_timestamp: datetime | date | None
    next_cursor: str | None


def to_page(result: CappedResult) -> dict:
    return {
        "rows": result.rows,
        "returned_count": result.returned_count,
        "truncated": result.truncated,
        "oldest_included_timestamp": result.oldest_included_timestamp,
        "next_cursor": encode_cursor(result.next_cursor),
    }
