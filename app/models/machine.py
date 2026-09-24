from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MachineModelModel(Base):
    """A machine model (product line), e.g. MDL-100. Machines reference it."""

    __tablename__ = "machine_model"

    id: Mapped[str] = mapped_column("model_id", String(30), primary_key=True)
    model_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    primitive_diameter: Mapped[int | None] = mapped_column(Integer)
    nominal_heads: Mapped[int | None] = mapped_column(Integer)
    container_type: Mapped[str | None] = mapped_column(String(200))
    cap_type: Mapped[str | None] = mapped_column(String(200))
    industry_segment: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)

    machines: Mapped[list["MachineModel"]] = relationship(back_populates="model")


class MachineModel(Base):
    """An installed machine owned by a company."""

    __tablename__ = "machine"

    id: Mapped[str] = mapped_column("machine_id", String(30), primary_key=True)
    company_id: Mapped[str] = mapped_column(
        ForeignKey("client.company_id"), nullable=False, index=True
    )
    model_id: Mapped[str] = mapped_column(ForeignKey("machine_model.model_id"), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    delivery_date: Mapped[date | None] = mapped_column(Date)
    plant_location: Mapped[str | None] = mapped_column(String(200))
    configuration_profile: Mapped[str | None] = mapped_column(Text)
    plc_family: Mapped[str | None] = mapped_column(String(50))
    software_version: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (
        CheckConstraint(
            "plc_family IN ('SIEMENS-SIMATIC-S7', 'LINE-PLC-INTEGRATED', 'HARDWIRED-CONTROL-PANEL')",
            name="ck_machine_plc_family",
        ),
    )

    model: Mapped["MachineModelModel"] = relationship(back_populates="machines")
