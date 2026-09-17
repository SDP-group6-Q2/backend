from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import ClientModel
from app.repositories import ClientRepository
from app.services.mcp_directory_client import lookup_company


class ClientService:
    def __init__(self, client_repository: ClientRepository):
        self.client_repository = client_repository

    async def get_clients(self) -> list[ClientModel]:
        return await self.client_repository.get_clients()

    async def get_client_by_id(self, client_id: str) -> ClientModel:
        client = await self.client_repository.get_client_by_id(client_id)
        if client is None:
            raise ValueError(f"Client with id '{client_id}' not found.")
        return client

    async def get_client_by_name(self, name: str) -> ClientModel:
        client = await self.client_repository.get_client_by_name(name)
        if client is None:
            raise ValueError(f"Client with name '{name}' not found.")
        return client

    async def create_client(self, name: str, company_id: str) -> ClientModel:
        existing_client = await self.client_repository.get_client_by_name(name)
        if existing_client:
            raise ValueError(f"Client with name '{name}' already exists.")

        company_profile = await lookup_company(company_id)
        if company_profile is None:
            raise ValueError(f"No fleet company found for company_id '{company_id}'.")

        return await self.client_repository.create_client(name, company_profile)

    async def delete_client(self, client_id: str) -> None:
        client = await self.client_repository.get_client_by_id(client_id)
        if client is None:
            raise ValueError(f"Client with id '{client_id}' not found.")
        await self.client_repository.delete_client(client_id)


def get_client_service(db_session: AsyncSession = Depends(get_db)) -> ClientService:
    return ClientService(ClientRepository(db_session))
