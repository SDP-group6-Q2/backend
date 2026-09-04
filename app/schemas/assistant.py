from datetime import datetime

from pydantic import BaseModel, ConfigDict

class ChatMessageRequest(BaseModel):
    machine_id: str
    message: str
    conversation_id: str | None = None

class ChatMessageResponse(BaseModel):
    user_id: str
    machine_id: str
    message: str
    answer: str
    conversation_id: str

class MessageRead(BaseModel):
    role: str
    content: str
    created_at: datetime

class ConversationHistory(BaseModel):
    conversation_id: str
    machine_id: str
    messages: list[MessageRead]
