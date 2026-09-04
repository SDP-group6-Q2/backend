import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConversationModel(Base):
    __tablename__ = "conversation"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    machine_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    messages: Mapped[list["MessageModel"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="MessageModel.created_at"
    )


class MessageModel(Base):
    __tablename__ = "message"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversation.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    conversation: Mapped["ConversationModel"] = relationship(back_populates="messages")
