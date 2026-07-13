import uuid
from datetime import datetime, timezone

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClientModel(Base):
    __tablename__ = "client"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    users: Mapped[list["UserModel"]] = relationship(back_populates="client")


class UserModel(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    # new users are inactive until a superuser activates them
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("client.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    client: Mapped["ClientModel"] = relationship(back_populates="users")
