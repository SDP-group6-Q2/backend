"""Values accepted by the ticket and alarm list filters. Each filter takes one or more values (repeat the query
parameter, e.g. `?priority=Critical&priority=High`); rows matching any of them are returned."""

from collections.abc import Sequence
from typing import Literal

# "open" is shorthand for every status of a ticket that still needs work.
TicketStatus = Literal["open", "Open", "In progress", "Waiting for parts", "Resolved", "Closed"]
OPEN_TICKET_STATUSES = ("Open", "In progress", "Waiting for parts")
TicketPriority = Literal["Critical", "High", "Medium", "Low"]

AlarmStatus = Literal["Open", "Acknowledged", "Resolved"]
AlarmSeverity = Literal["Critical", "High", "Medium", "Low"]


def ticket_statuses(values: Sequence[str] | None) -> list[str] | None:
    """The stored statuses to match, with "open" expanded; None means no status filter."""
    if not values:
        return None
    expanded: list[str] = []
    for value in values:
        for status in OPEN_TICKET_STATUSES if value == "open" else (value,):
            if status not in expanded:
                expanded.append(status)
    return expanded
