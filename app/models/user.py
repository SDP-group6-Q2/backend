import uuid
from datetime import datetime, timezone

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClientModel(Base):
    __tablename__ = "client"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=True)
    sector: Mapped[str] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=True)

    users: Mapped[list["UserModel"]] = relationship(back_populates="client")


class UserModel(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    # new users are inactive until a superuser activates them
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("client.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    job_title: Mapped[str] = mapped_column(String(100), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "visibility IN ('full', 'technician', 'commercial')",
            name="ck_user_visibility",
        ),
    )

    client: Mapped["ClientModel"] = relationship(back_populates="users", lazy="joined")
