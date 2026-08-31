from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import current_active_user
from app.models import UserModel
from app.schemas import ChatRequest, ChatResponse, ConversationHistory, MessageRead
from app.services import get_chat_service, ChatService


router = APIRouter(dependencies=[Depends(current_active_user)])

@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    message: ChatRequest,
    user: UserModel = Depends(current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        conversation_id, answer = await chat_service.send_message(
            message.machine_id, user, message.message, message.conversation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while asking the assistant: {e}"
        )

    return ChatResponse(
        conversation_id=conversation_id,
        machine_id=message.machine_id,
        message=message.message,
        answer=answer,
    )

@router.get("/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(
    conversation_id: str,
    user: UserModel = Depends(current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        conversation = await chat_service.get_history(conversation_id, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ConversationHistory(
        conversation_id=str(conversation.id),
        machine_id=conversation.machine_id,
        messages=[
            MessageRead(role=m.role, content=m.content, created_at=m.created_at)
            for m in conversation.messages
        ],
    )
