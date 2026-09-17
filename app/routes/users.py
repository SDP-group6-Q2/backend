import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users.exceptions import UserAlreadyExists, UserNotExists

from app.core.auth import current_active_user, current_superuser

from app.models import UserModel
from app.schemas import OwnPasswordUpdate, UserCreate, UserRead, UserUpdate
from app.services import UserManager, get_user_manager
from app.services.mcp_directory_client import lookup_user

router = APIRouter()


async def _build_user_read(user: UserModel) -> UserRead:
    """Merges live fleet-profile fields (company_id/first_name/last_name/job_title/
    visibility) from mcp-server into the response -- these are never stored
    locally, only fetched via user_id at the moment a profile is actually read."""
    fleet_user = await lookup_user(user.user_id) if user.user_id else None
    return UserRead(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        user_id=user.user_id,
        username=user.username,
        company_id=(fleet_user or {}).get("company_id"),
        first_name=(fleet_user or {}).get("first_name"),
        last_name=(fleet_user or {}).get("last_name"),
        job_title=(fleet_user or {}).get("job_title"),
        visibility=(fleet_user or {}).get("visibility"),
    )


# --- self-service: a user may view its own profile and change its own password only ---


@router.get("/me", response_model=UserRead)
async def read_own_profile(user: UserModel = Depends(current_active_user)) -> UserRead:
    return await _build_user_read(user)


@router.patch("/me", response_model=UserRead)
async def update_own_password(
    password_update: OwnPasswordUpdate,
    user: UserModel = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
) -> UserRead:
    updated_user = await user_manager.update(
        UserUpdate(password=password_update.password), user, safe=True
    )
    return await _build_user_read(updated_user)


# --- superuser-only: everything else (create, view/update/delete any user, activation) ---

admin_router = APIRouter(dependencies=[Depends(current_superuser)])


async def _validate_fleet_user_id(fleet_user_id: str) -> None:
    """Confirm fleet_user_id exists in mcp-server's fleet dataset -- a
    data-integrity check catching an obvious typo early, not the actual
    authorization boundary (mcp-server independently derives a user's real
    company/visibility from user_id on every tool call, regardless of
    whether this check ran)."""
    fleet_user = await lookup_user(fleet_user_id)
    if fleet_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No fleet user found for user_id '{fleet_user_id}'.",
        )


@admin_router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserRead:
    if user_create.user_id is not None:
        await _validate_fleet_user_id(user_create.user_id)

    try:
        new_user = await user_manager.create(user_create, safe=False)
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    return await _build_user_read(new_user)


@admin_router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserRead:
    try:
        user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await _build_user_read(user)


@admin_router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserRead:
    try:
        user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.user_id is not None:
        await _validate_fleet_user_id(user_update.user_id)

    updated_user = await user_manager.update(user_update, user, safe=False)
    return await _build_user_read(updated_user)


@admin_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    user_manager: UserManager = Depends(get_user_manager),
) -> None:
    try:
        user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await user_manager.delete(user)


@admin_router.post("/{user_id}/activate", response_model=UserRead)
async def activate_user(
    user_id: uuid.UUID,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserRead:
    try:
        user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_user = await user_manager.update(UserUpdate(is_active=True), user, safe=False)
    return await _build_user_read(updated_user)

@admin_router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: uuid.UUID,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserRead:
    try:
        user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_user = await user_manager.update(UserUpdate(is_active=False), user, safe=False)
    return await _build_user_read(updated_user)


router.include_router(admin_router)
