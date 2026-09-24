import uuid

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models import ConversationModel, MessageModel, UserModel
from app.repositories import ConversationRepository


class AssistantUnavailableError(Exception):
    """The orchestrator could not be reached or returned an error."""


class AssistantTimeoutError(AssistantUnavailableError):
    """The orchestrator did not answer in time."""


class AssistantService:
    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

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

    @staticmethod
    async def _call_orchestrator(
        question: str, user_id: str, machine_id: str, history: list[dict[str, str]]
    ) -> str:
        try:
            async with httpx.AsyncClient(timeout=settings.orchestrator_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.orchestrator_url}/chat",
                    json={
                        "question": question,
                        "user_id": user_id,
                        "machine_id": machine_id,
                        "history": history,
                    },
                )
                response.raise_for_status()
        except httpx.TimeoutException as e:
            raise AssistantTimeoutError("The assistant took too long to answer.") from e
        except httpx.HTTPError as e:
            raise AssistantUnavailableError(f"The assistant is unavailable: {e!r}") from e
        return response.json()["answer"]

    async def ask_assistant(self, machine_id: str, user: UserModel, message: str, conversation_id: str | None = None) -> tuple[str, str]:
        """Ask the assistant, appending to conversation_id's history if given. Returns (conversation_id, answer)."""
        if user.user_id is None:
            raise PermissionError("This user has no assistant user_id assigned.")

        conversation, messages = await self._get_or_create_conversation(user, machine_id, conversation_id)
        history = self._history_from_messages(messages)

        answer = await self._call_orchestrator(message, user.user_id, machine_id, history)

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
