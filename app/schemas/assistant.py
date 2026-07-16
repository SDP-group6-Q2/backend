from pydantic import BaseModel, ConfigDict

class ChatMessageRequest(BaseModel):
    machine_id: str
    message: str

class ChatMessageResponse(BaseModel):
    user_id: str
    machine_id: str
    message: str
    answer: str