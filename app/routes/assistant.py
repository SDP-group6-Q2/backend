from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.core.auth import current_active_user
from app.core.exceptions import AccessDeniedError
from app.models import UserModel
from app.schemas import ChatMessageRequest, ChatMessageResponse, ConversationHistory, MessageRead
from app.services import get_assistant_service, AssistantService
from app.services.assistant_service import AssistantTimeoutError, AssistantUnavailableError


router = APIRouter(dependencies=[Depends(current_active_user)])

@router.post("/")
async def ask_assistant(
    message: ChatMessageRequest,
    user: UserModel = Depends(current_active_user),
    assistant_service: AssistantService = Depends(get_assistant_service),
    # current_active_user has already validated this token; the assistant forwards it so that the data
    # tools run with this user's own permissions.
    authorization: str = Header(),
):
    try:
        conversation_id, answer = await assistant_service.ask_assistant(
            message.machine_id, user, message.message, message.conversation_id, authorization
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
    except AccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AssistantTimeoutError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except AssistantUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while asking the assistant: {e}"
        )

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
