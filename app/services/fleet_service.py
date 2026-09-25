from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccessDeniedError, NotFoundError
from app.db.session import get_db
from app.models import MachineModel, UserModel
from app.repositories import MachineRepository

# Machines, machine models and manuals are identity/documentation data: visible to every tier.
_MACHINE_IDENTITY_VISIBILITIES = {"full", "technician", "commercial"}


class FleetService:
    def __init__(self, machine_repository: MachineRepository):
        self.machine_repository = machine_repository

    @staticmethod
    def _authorized_company_id(user: UserModel) -> str:
        company_id = user.client.company_id if user.client else None
        if company_id is None or user.visibility not in _MACHINE_IDENTITY_VISIBILITIES:
            raise AccessDeniedError("You cannot access machine information.")
        return company_id

    async def get_company_machines(self, user: UserModel) -> list[MachineModel]:
        """Every machine of the user's company, including its model."""
        company_id = self._authorized_company_id(user)
        return await self.machine_repository.list_machines(company_id)

    async def get_machine(self, user: UserModel, machine_id: str) -> MachineModel:
        company_id = self._authorized_company_id(user)
        machine = await self.machine_repository.get_machine(machine_id, company_id)
        if machine is None:
            raise NotFoundError(f"Machine '{machine_id}' not found.")
        return machine


def get_fleet_service(db_session: AsyncSession = Depends(get_db)) -> FleetService:
    return FleetService(MachineRepository(db_session))
