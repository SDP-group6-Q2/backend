from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AlarmModel(Base):
    __tablename__ = "alarm"

    id: Mapped[str] = mapped_column("alarm_id", String(30), primary_key=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machine.machine_id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    alarm_code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    alarm_status: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        Index("ix_alarm_machine_timestamp", "machine_id", "timestamp"),
        CheckConstraint("severity IN ('Critical', 'High', 'Medium', 'Low')", name="ck_alarm_severity"),
        CheckConstraint(
            "alarm_status IN ('Open', 'Acknowledged', 'Resolved')", name="ck_alarm_status"
        ),
    )
