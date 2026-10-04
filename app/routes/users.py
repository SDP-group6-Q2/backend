import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users.exceptions import UserAlreadyExists, UserNotExists

from app.core.auth import current_active_user, current_superuser

from app.models import UserModel
from app.schemas import OwnPasswordUpdate, UserCreate, UserRead, UserUpdate
from app.services import UserManager, get_user_manager

router = APIRouter()


# --- self-service: a user may view its own profile and change its own password only ---


@router.get("/me", response_model=UserRead)
async def read_own_profile(user: UserModel = Depends(current_active_user)) -> UserModel:
    return user


@router.patch("/me", response_model=UserRead)
async def update_own_password(
    password_update: OwnPasswordUpdate,
    user: UserModel = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
) -> UserModel:
    return await user_manager.update(
        UserUpdate(password=password_update.password), user, safe=True
    )


# --- superuser-only: everything else (create, view/update/delete any user, activation) ---

admin_router = APIRouter(dependencies=[Depends(current_superuser)])


@admin_router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserModel:
    try:
        return await user_manager.create(user_create, safe=False)
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )


@admin_router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserModel:
    try:
        return await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@admin_router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserModel:
    try:
        user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await user_manager.update(user_update, user, safe=False)


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
) -> UserModel:
    try:
        user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await user_manager.update(UserUpdate(is_active=True), user, safe=False)

@admin_router.post("/{user_id}/deactivate", response_model=UserRead)
async def deactivate_user(
    user_id: uuid.UUID,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserModel:
    try:
        user = await user_manager.get(user_id)
    except UserNotExists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await user_manager.update(UserUpdate(is_active=False), user, safe=False)


router.include_router(admin_router)
