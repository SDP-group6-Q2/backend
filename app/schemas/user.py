import uuid

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    client_id: uuid.UUID
    user_id: str | None = None
    username: str
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None


class UserCreate(schemas.BaseUserCreate):
    is_active: bool = False
    client_id: uuid.UUID
    # Bridge key into mcp-server's fleet dataset (assistant.users.userid), validated
    # in app/routes/users.py before creation. Optional -- staff/superuser accounts
    # legitimately have no fleet identity.
    user_id: str | None = None
    username: str
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    user_id: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None


class OwnPasswordUpdate(BaseModel):
    """Self-service schema: a user may only ever change their own password."""

    password: str
