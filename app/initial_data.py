"""Creates the first superuser from env variables. Safe to run multiple times."""

import asyncio
import logging

from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import UserAlreadyExists
from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_maker
from app.models.user import ClientModel, UserModel
from app.schemas.user import UserCreate
from app.services.user_manager import UserManager

logger = logging.getLogger(__name__)


async def create_first_superuser() -> None:
    if not settings.first_superuser_email or not settings.first_superuser_password:
        logger.info(
            "FIRST_SUPERUSER_EMAIL/FIRST_SUPERUSER_PASSWORD not set, skipping superuser creation"
        )
        return

    async with async_session_maker() as session:
        client = (
            await session.execute(
                select(ClientModel).where(
                    ClientModel.name == settings.first_superuser_client_name
                )
            )
        ).scalar_one_or_none()

        if client is None:
            client = ClientModel(name=settings.first_superuser_client_name)
            session.add(client)
            await session.commit()
            await session.refresh(client)

        user_manager = UserManager(SQLAlchemyUserDatabase(session, UserModel))

        try:
            await user_manager.create(
                UserCreate(
                    email=settings.first_superuser_email,
                    password=settings.first_superuser_password,
                    username=settings.first_superuser_username,
                    client_id=client.id,
                    is_active=True,
                    is_superuser=True,
                ),
                safe=False,
            )
            logger.info("Created first superuser %s", settings.first_superuser_email)
        except UserAlreadyExists:
            logger.info("Superuser %s already exists, skipping", settings.first_superuser_email)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(create_first_superuser())
