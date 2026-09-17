from datetime import datetime, timezone

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserModel(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    # new users are inactive until a superuser activates them
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Bridge key into mcp-server's `assistant` database (assistant.users.userid) --
    # the fleet dataset is the sole source of truth for what company/visibility tier/
    # first_name/last_name/job_title this maps to; validated against it at creation
    # time (see app/routes/users.py) and fetched live via
    # app/services/mcp_directory_client.lookup_user when needed for display, never
    # mirrored locally (including company: there is no separate company_id column
    # here -- it's derived transitively through user_id whenever needed). Nullable:
    # staff/superuser accounts legitimately have no fleet identity.
    user_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
