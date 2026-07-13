import uuid

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    client_id: uuid.UUID
    username: str


class UserCreate(schemas.BaseUserCreate):
    is_active: bool = False
    client_id: uuid.UUID
    username: str


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = None


class OwnPasswordUpdate(BaseModel):
    """Self-service schema: a user may only ever change their own password."""

    password: str
