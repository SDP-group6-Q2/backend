from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    machine_id: str
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    machine_id: str
    message: str
    answer: str


class MessageRead(BaseModel):
    role: str
    content: str
    created_at: datetime


class ConversationHistory(BaseModel):
    conversation_id: str
    machine_id: str
    messages: list[MessageRead]
