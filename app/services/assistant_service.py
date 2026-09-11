import os
import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import assistant_bootstrap  # noqa: F401  (adds assistant/ to sys.path so its `src.*` imports resolve)
from src.FleetAssistant import FleetAssistant

from app.db.session import get_db
from app.models import ConversationModel, MessageModel, UserModel
from app.repositories import ConversationRepository

class AssistantService:
    def __init__(self, conversation_repository: ConversationRepository, assistant: FleetAssistant | None = None):
        self.conversation_repository = conversation_repository
        llama_model = os.getenv("LLAMA_MODEL", "gpt-oss:20b-cloud")
        llama_base_url = os.getenv("LLAMA_BASE_URL", "http://localhost:11434")
        self.assistant = assistant if assistant is not None else FleetAssistant(model=llama_model, llama_base_url=llama_base_url)

    async def _get_or_create_conversation(
        self, user: UserModel, machine_id: str, conversation_id: str | None
    ) -> tuple[ConversationModel, list[MessageModel]]:
        if not conversation_id:
            conversation = await self.conversation_repository.create_conversation(str(user.id), machine_id)
            return conversation, []

        try:
            uuid.UUID(conversation_id)
        except ValueError:
            raise ValueError(f"Conversation with id '{conversation_id}' not found.")

        conversation = await self.conversation_repository.get_conversation_by_id(conversation_id)
        if conversation is None or str(conversation.user_id) != str(user.id):
            raise ValueError(f"Conversation with id '{conversation_id}' not found.")
        return conversation, conversation.messages

    @staticmethod
    def _history_from_messages(messages: list[MessageModel]) -> list[dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in messages]

    async def ask_assistant(self, machine_id: str, user: UserModel, message: str, conversation_id: str | None = None) -> tuple[str, str]:
        """Ask the assistant, appending to conversation_id's history if given. Returns (conversation_id, answer)."""
        conversation, messages = await self._get_or_create_conversation(user, machine_id, conversation_id)
        history = self._history_from_messages(messages)

        try:
            answer = self.assistant.ask(message, user.user_id, machine_id, history=history)
        except Exception as e:
            raise Exception(f"Error while asking the assistant: {e}")

        await self.conversation_repository.add_message(str(conversation.id), "user", message)
        await self.conversation_repository.add_message(str(conversation.id), "assistant", answer)

        return str(conversation.id), answer

    async def get_history(self, conversation_id: str, user: UserModel) -> ConversationModel:
        try:
            uuid.UUID(conversation_id)
        except ValueError:
            raise ValueError(f"Conversation with id '{conversation_id}' not found.")

        conversation = await self.conversation_repository.get_conversation_by_id(conversation_id)
        if conversation is None or str(conversation.user_id) != str(user.id):
            raise ValueError(f"Conversation with id '{conversation_id}' not found.")
        return conversation

def get_assistant_service(db_session: AsyncSession = Depends(get_db)) -> AssistantService:
    return AssistantService(ConversationRepository(db_session))
