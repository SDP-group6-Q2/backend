from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TelemetrySnapshotModel(Base):
    """One hour of aggregated measurements for one machine."""

    __tablename__ = "telemetry_snapshot"

    id: Mapped[str] = mapped_column("telemetry_id", String(30), primary_key=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machine.machine_id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    operational_status: Mapped[str] = mapped_column(String(20), nullable=False)
    production_rate_bph: Mapped[float | None] = mapped_column(Float)
    uptime_percentage: Mapped[float | None] = mapped_column(Float)
    alarm_count: Mapped[int | None] = mapped_column(Integer)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    energy_kwh: Mapped[float | None] = mapped_column(Float)
    health_note: Mapped[str | None] = mapped_column(String(300))

    __table_args__ = (
        Index("ix_telemetry_snapshot_machine_timestamp", "machine_id", "timestamp"),
        CheckConstraint(
            "operational_status IN ('Running', 'Alarm', 'Idle', 'Stopped', 'Maintenance', 'Size change')",
            name="ck_telemetry_operational_status",
        ),
    )
