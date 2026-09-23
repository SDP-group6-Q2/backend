import os
import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import assistant_bootstrap  # noqa: F401  (adds assistant/ to sys.path so its `src.*` imports resolve)
from src.FleetAssistant import FleetAssistant
from src.storage.manual_documents import get_manual_url as get_manual_signed_url

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

    async def ask_assistant(
        self,
        machine_id: str,
        user: UserModel,
        message: str,
        auth_token: str,
        conversation_id: str | None = None,
    ) -> tuple[str, str]:
        """Ask the assistant, appending to conversation_id's history if given. Returns (conversation_id, answer).

        `auth_token` is the caller's own JWT, forwarded down to FleetAssistant
        so its MCP client can present it to the gateway on every tool call --
        the gateway derives trusted identity from this same token rather than
        from anything the LLM could influence.
        """
        conversation, messages = await self._get_or_create_conversation(user, machine_id, conversation_id)
        history = self._history_from_messages(messages)

        try:
            if not user:
                raise ValueError("User not found.")
            print("Asking:", message, "from user:", user.user_id, "about machine:", machine_id)
            answer = await self.assistant.aask(message, user.user_id, machine_id, auth_token, history=history)
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

    def get_manual_url(self, machine_id: str, user: UserModel) -> str:
        """Return a short-lived signed URL for machine_id's manual PDF. Raises
        ValueError if the user isn't authorized for that machine or no manual
        is on file -- same tenant/visibility check the manuals RAG tool uses."""
        url = get_manual_signed_url(user.user_id, machine_id)
        if url is None:
            raise ValueError(f"No manual available for machine_id '{machine_id}'.")
        return url

def get_assistant_service(db_session: AsyncSession = Depends(get_db)) -> AssistantService:
    return AssistantService(ConversationRepository(db_session))
