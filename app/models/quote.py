from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QuoteModel(Base):
    __tablename__ = "quote"

    id: Mapped[str] = mapped_column("quote_id", String(30), primary_key=True)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("client.company_id"), nullable=False, index=True
    )
    currency: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)

    revisions: Mapped[list["QuoteRevisionModel"]] = relationship(
        back_populates="quote", order_by="QuoteRevisionModel.revision_number"
    )


class QuoteRevisionModel(Base):
    __tablename__ = "quote_revision"

    id: Mapped[str] = mapped_column("quote_revision_id", String(30), primary_key=True)
    quote_id: Mapped[str] = mapped_column(ForeignKey("quote.quote_id"), nullable=False, index=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    revision_status: Mapped[str] = mapped_column(String(20), nullable=False)
    issued_at: Mapped[date | None] = mapped_column(Date)
    discount_rate: Mapped[float | None] = mapped_column(Float)
    change_summary: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("quote_id", "revision_number", name="uq_quote_revision_number"),
        CheckConstraint(
            "revision_status IN ('Draft', 'Submitted', 'Superseded', 'Approved', 'Rejected', 'Expired')",
            name="ck_quote_revision_status",
        ),
    )

    quote: Mapped["QuoteModel"] = relationship(back_populates="revisions")
    lines: Mapped[list["QuoteLineModel"]] = relationship(back_populates="revision")


class QuoteLineModel(Base):
    __tablename__ = "quote_line"

    id: Mapped[str] = mapped_column("quote_line_id", String(30), primary_key=True)
    quote_revision_id: Mapped[str] = mapped_column(
        ForeignKey("quote_revision.quote_revision_id"), nullable=False, index=True
    )
    # Empty on lines that don't refer to an installed machine.
    machine_id: Mapped[str | None] = mapped_column(ForeignKey("machine.machine_id"))
    # Already net of the parent revision's discount_rate.
    price: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)

    revision: Mapped["QuoteRevisionModel"] = relationship(back_populates="lines")
