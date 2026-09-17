import uuid

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    user_id: str | None = None
    username: str
    # Not ORM-backed -- populated live from mcp-server (app/services/mcp_directory_client
    # .lookup_user) by the route when user_id is set, None otherwise. Never stored.
    # company_id is derived transitively through user_id -- there is no separate
    # stored company/client concept in backend at all.
    company_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    visibility: str | None = None


class UserCreate(schemas.BaseUserCreate):
    is_active: bool = False
    # Bridge key into mcp-server's fleet dataset (assistant.users.userid), validated
    # in app/routes/users.py before creation. Optional -- staff/superuser accounts
    # legitimately have no fleet identity. company_id/first_name/last_name/job_title/
    # visibility are not accepted here -- they live in mcp-server, fetched live via
    # user_id.
    user_id: str | None = None
    username: str


class UserUpdate(schemas.BaseUserUpdate):
    user_id: str | None = None
    username: str | None = None


class OwnPasswordUpdate(BaseModel):
    """Self-service schema: a user may only ever change their own password."""

    password: str
