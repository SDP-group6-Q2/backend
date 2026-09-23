from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import current_active_user, get_raw_bearer_token
from app.models import UserModel
from app.schemas import ChatMessageRequest, ChatMessageResponse, ConversationHistory, MessageRead
from app.services import get_assistant_service, AssistantService


router = APIRouter(dependencies=[Depends(current_active_user)])

@router.post("/")
async def ask_assistant(
    message: ChatMessageRequest,
    user: UserModel = Depends(current_active_user),
    auth_token: str = Depends(get_raw_bearer_token),
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    try:
        conversation_id, answer = await assistant_service.ask_assistant(
            message.machine_id, user, message.message, auth_token, message.conversation_id
        )
        return ChatMessageResponse(
            user_id=str(user.id),
            machine_id=message.machine_id,
            message=message.message,
            answer=answer,
            conversation_id=conversation_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while asking the assistant: {e}"
        )

@router.get("/manuals/{machine_id}")
async def get_manual(
    machine_id: str,
    user: UserModel = Depends(current_active_user),
    assistant_service: AssistantService = Depends(get_assistant_service),
):
    try:
        url = assistant_service.get_manual_url(machine_id, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"url": url}

@router.get("/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(
    conversation_id: str,
    user: UserModel = Depends(current_active_user),
    assistant_service: AssistantService = Depends(get_assistant_service),
):
    try:
        conversation = await assistant_service.get_history(conversation_id, user)
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
