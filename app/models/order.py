from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrderModel(Base):
    __tablename__ = "customer_order"  # "order" is a reserved word

    id: Mapped[str] = mapped_column("order_id", String(30), primary_key=True)
    quote_id: Mapped[str | None] = mapped_column(ForeignKey("quote.quote_id"), index=True)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("client.company_id"), nullable=False, index=True
    )
    order_status: Mapped[str] = mapped_column(String(20), nullable=False)
    order_date: Mapped[date | None] = mapped_column(Date)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date)
    shipment_status: Mapped[str | None] = mapped_column(String(30))
    currency: Mapped[str | None] = mapped_column(String(10))
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "order_status IN ('Confirmed', 'In production', 'Delivered', 'Closed')",
            name="ck_order_status",
        ),
        CheckConstraint(
            "shipment_status IN ('In production', 'Ready for shipment', 'Delivered', 'Installed')",
            name="ck_order_shipment_status",
        ),
    )

    lines: Mapped[list["OrderLineModel"]] = relationship(back_populates="order")


class OrderLineModel(Base):
    """Tracks fulfilment only: no item, quantity or price (those come from the quote lines)."""

    __tablename__ = "order_line"

    id: Mapped[str] = mapped_column("order_line_id", String(30), primary_key=True)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("customer_order.order_id"), nullable=False, index=True
    )
    fulfillment_status: Mapped[str] = mapped_column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "fulfillment_status IN ('Manufacturing', 'Ready for shipment', 'Delivered')",
            name="ck_order_line_fulfillment_status",
        ),
    )

    order: Mapped["OrderModel"] = relationship(back_populates="lines")
