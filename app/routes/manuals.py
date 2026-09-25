from fastapi import APIRouter, Depends

from app.core.auth import current_active_user
from app.models import UserModel
from app.schemas import ManualRead, ManualUrlRead
from app.services import ManualService, get_manual_service

router = APIRouter(dependencies=[Depends(current_active_user)])


@router.get("/", response_model=list[ManualRead])
async def list_manuals(
    user: UserModel = Depends(current_active_user),
    manual_service: ManualService = Depends(get_manual_service),
):
    """Machines of the user's company that have a manual."""
    return await manual_service.list_manuals(user)


@router.get("/{machine_id}", response_model=ManualUrlRead)
async def get_manual_url(
    machine_id: str,
    user: UserModel = Depends(current_active_user),
    manual_service: ManualService = Depends(get_manual_service),
):
    """A short-lived signed URL for the machine's manual PDF."""
    return await manual_service.get_manual_url(user, machine_id)
