from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClientModel


class ClientRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_clients(self) -> list[ClientModel]:
        result = await self.db_session.execute(select(ClientModel))
        return list(result.scalars().all())

    async def get_client_by_name(self, name: str) -> ClientModel | None:
        result = await self.db_session.execute(
            select(ClientModel).where(ClientModel.name == name)
        )
        return result.scalar_one_or_none()

    async def create_client(self, name: str) -> ClientModel:
        try:
            new_client = ClientModel(name=name)
            self.db_session.add(new_client)
            await self.db_session.commit()
            await self.db_session.refresh(new_client)
            return new_client
        except Exception:
            await self.db_session.rollback()
            raise

    async def delete_client(self, client_id: str) -> None:
        client = await self.get_client_by_id(client_id)
        if client:
            await self.db_session.delete(client)
            await self.db_session.commit()

    async def get_client_by_id(self, client_id: str) -> ClientModel | None:
        result = await self.db_session.execute(
            select(ClientModel).where(ClientModel.id == client_id)
        )
        return result.scalar_one_or_none()
