from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ConversationModel, MessageModel


class ConversationRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_conversation_by_id(self, conversation_id: str) -> ConversationModel | None:
        result = await self.db_session.execute(
            select(ConversationModel)
            .where(ConversationModel.id == conversation_id)
            .options(selectinload(ConversationModel.messages))
        )
        return result.scalar_one_or_none()

    async def create_conversation(self, user_id: str, machine_id: str) -> ConversationModel:
        conversation = ConversationModel(user_id=user_id, machine_id=machine_id)
        self.db_session.add(conversation)
        await self.db_session.commit()
        await self.db_session.refresh(conversation)
        return conversation

    async def add_message(
        self, conversation_id: str, role: str, content: str, trace: list | None = None
    ) -> MessageModel:
        message = MessageModel(conversation_id=conversation_id, role=role, content=content, trace=trace)
        self.db_session.add(message)
        await self.db_session.commit()
        await self.db_session.refresh(message)
        return message
