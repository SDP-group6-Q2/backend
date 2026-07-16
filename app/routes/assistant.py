from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import current_active_user
from app.models import UserModel
from app.schemas import ChatMessageRequest, ChatMessageResponse
from app.services import get_assistant_service, AssistantService


router = APIRouter(dependencies=[Depends(current_active_user)])

@router.post("/")
async def ask_assistant(
    message: ChatMessageRequest,
    user: UserModel = Depends(current_active_user),
    assistant_service: AssistantService = Depends(get_assistant_service)
):
    try:
        answer = assistant_service.ask_assistant(message.machine_id, user, message.message)
        return ChatMessageResponse(
            user_id=str(user.id),
            machine_id=message.machine_id,
            message=message.message,
            answer=answer
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while asking the assistant: {e}"
        )