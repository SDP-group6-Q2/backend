from datetime import date

from pydantic import BaseModel, ConfigDict


class QuoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    currency: str | None
    created_at: date | None
    valid_until: date | None
    description: str | None


class QuoteRevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quote_id: str
    revision_number: int
    revision_status: str
    issued_at: date | None
    discount_rate: float | None
    change_summary: str | None


class QuoteLineRead(BaseModel):
    """`price` is already net of the revision's discount_rate, in `currency` (the quote's). `machine_id` is
    null on lines that don't refer to an installed machine."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    quote_revision_id: str
    machine_id: str | None
    price: float | None
    currency: str | None = None
    description: str | None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    quote_id: str | None
    company_id: str
    order_status: str
    order_date: date | None
    expected_delivery_date: date | None
    shipment_status: str | None
    currency: str | None
    notes: str | None


class QuoteOverviewRow(BaseModel):
    """One quote with its current state in a single row: the latest revision (a quote's status is its latest
    revision's), that revision's line count and net total, and the orders created from the quote. `net_total` is
    already net of the discount, in `currency`; it is null when the revision has no priced lines."""

    id: str
    currency: str | None
    created_at: date | None
    valid_until: date | None
    description: str | None
    latest_revision_id: str | None
    latest_revision_number: int | None
    status: str | None
    discount_rate: float | None
    line_count: int
    net_total: float | None
    order_ids: list[str]


class OrderOverviewRow(OrderRead):
    """An order with its value: what was ordered is the approved revision of its quote (the highest-numbered
    Approved one), so `quote_revision_id`, `line_count` and `net_total` come from that revision. They are
    null/0 when the quote has no approved revision."""

    quote_revision_id: str | None
    line_count: int
    net_total: float | None


class OrderLineRead(BaseModel):
    """Fulfilment only: an order's content comes from the quote lines of its approved revision."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    fulfillment_status: str
