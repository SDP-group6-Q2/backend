from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.alarm import AlarmModel


class MaintenanceTicketModel(Base):
    __tablename__ = "maintenance_ticket"

    id: Mapped[str] = mapped_column("ticket_id", String(30), primary_key=True)
    machine_id: Mapped[str] = mapped_column(
        ForeignKey("machine.machine_id"), nullable=False, index=True
    )
    # Empty on tickets that did not originate from an alarm.
    alarm_id: Mapped[str | None] = mapped_column(ForeignKey("alarm.alarm_id"))
    ticket_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ticket_status: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    created_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    owner_role: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (
        CheckConstraint(
            "ticket_type IN ('Remote troubleshooting', 'On-site service', 'Spare parts request', "
            "'Scheduled maintenance', 'Overhaul', 'Size change assistance')",
            name="ck_ticket_type",
        ),
        CheckConstraint(
            "ticket_status IN ('Open', 'In progress', 'Waiting for parts', 'Resolved', 'Closed')",
            name="ck_ticket_status",
        ),
        CheckConstraint("priority IN ('Critical', 'High', 'Medium', 'Low')", name="ck_ticket_priority"),
        CheckConstraint(
            "owner_role IN ('Line Operator', 'Maintenance Man', 'Plant Maintenance Manager', "
            "'AROL Technical Service')",
            name="ck_ticket_owner_role",
        ),
    )

    alarm: Mapped["AlarmModel | None"] = relationship()
