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
    """`price` is already net of the revision's discount_rate. `machine_id` is null on lines
    that don't refer to an installed machine."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    quote_revision_id: str
    machine_id: str | None
    price: float | None
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


class OrderLineRead(BaseModel):
    """Fulfilment only: an order's content comes from the quote lines of its approved revision."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    fulfillment_status: str
