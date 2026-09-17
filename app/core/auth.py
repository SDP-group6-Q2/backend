import uuid

from fastapi import HTTPException, Request, status
from fastapi_users import FastAPIUsers, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.jwt import generate_jwt

from app.core.config import settings
from app.models.user import UserModel
from app.services.user_manager import get_user_manager

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


class AssistantAwareJWTStrategy(JWTStrategy[models.UP, models.ID]):
    """Stock JWTStrategy encodes only `sub` (the fastapi-users UUID primary
    key) and `aud`. The MCP gateway needs the assistant-domain `user_id` (a
    separate short string column -- see UserModel.user_id) to authorize
    against the `assistant` database's `users` table, which the UUID `sub`
    can't resolve on its own. This subclass adds that one extra claim;
    `read_token` (used by `current_active_user`/`current_superuser`) is
    inherited unchanged and ignores it."""

    async def write_token(self, user: models.UP) -> str:
        data = {
            "sub": str(user.id),
            "aud": self.token_audience,
            "user_id": getattr(user, "user_id", None),
        }
        return generate_jwt(data, self.encode_key, self.lifetime_seconds, algorithm=self.algorithm)


def get_jwt_strategy() -> JWTStrategy:
    return AssistantAwareJWTStrategy(
        secret=settings.jwt_secret,
        lifetime_seconds=settings.access_token_lifetime_seconds,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[UserModel, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)


def get_raw_bearer_token(request: Request) -> str:
    """The raw JWT string for the current request, forwarded as-is to the MCP
    gateway (see AssistantService.ask_assistant) -- `current_active_user`
    only exposes the decoded user, not the token itself."""
    auth_header = request.headers.get("Authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")
    return token
