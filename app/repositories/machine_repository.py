from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import MachineModel


class MachineRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def list_machines(self, company_id: str) -> list[MachineModel]:
        result = await self.db_session.execute(
            select(MachineModel)
            .where(MachineModel.company_id == company_id)
            .options(joinedload(MachineModel.model))
            .order_by(MachineModel.id)
        )
        return list(result.scalars().all())

    async def get_machine(self, machine_id: str, company_id: str) -> MachineModel | None:
        result = await self.db_session.execute(
            select(MachineModel)
            .where(MachineModel.id == machine_id, MachineModel.company_id == company_id)
            .options(joinedload(MachineModel.model))
        )
        return result.scalar_one_or_none()

    async def list_machines_with_manual(self, company_id: str) -> list[MachineModel]:
        result = await self.db_session.execute(
            select(MachineModel)
            .where(MachineModel.company_id == company_id, MachineModel.storage_path.is_not(None))
            .order_by(MachineModel.id)
        )
        return list(result.scalars().all())

    async def set_storage_path_by_serial(self, serial_number: str, storage_path: str) -> int:
        """Returns how many machines matched the serial number."""
        result = await self.db_session.execute(
            update(MachineModel)
            .where(MachineModel.serial_number == serial_number)
            .values(storage_path=storage_path)
        )
        await self.db_session.commit()
        return result.rowcount

    async def get_machine_company_id(self, machine_id: str) -> str | None:
        result = await self.db_session.execute(
            select(MachineModel.company_id).where(MachineModel.id == machine_id)
        )
        return result.scalar_one_or_none()
