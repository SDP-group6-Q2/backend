from datetime import date

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccessDeniedError
from app.db.session import get_db
from app.core.pagination import MAX_ROWS, CappedResult, Cursor, cap_rows, clamp_limit
from app.models import MaintenanceTicketModel, UserModel
from app.repositories import MachineRepository, MaintenanceRepository

# Maintenance tickets are operational data: technician/full only.
_OPERATIONAL_VISIBILITIES = {"full", "technician"}


class MaintenanceService:
    def __init__(
        self,
        machine_repository: MachineRepository,
        maintenance_repository: MaintenanceRepository,
    ):
        self.machine_repository = machine_repository
        self.maintenance_repository = maintenance_repository

    @staticmethod
    def _authorized_company_id(user: UserModel) -> str:
        company_id = user.client.company_id if user.client else None
        if company_id is None or user.visibility not in _OPERATIONAL_VISIBILITIES:
            raise AccessDeniedError("You cannot access operational data.")
        return company_id

    async def get_company_tickets(
        self,
        user: UserModel,
        since: date | None = None,
        until: date | None = None,
        limit: int = MAX_ROWS,
        before: Cursor | None = None,
    ) -> CappedResult[MaintenanceTicketModel]:
        """Tickets of the company's machines, newest first, capped at `limit` (max 100). Range matches
        createdDate. When truncated, pass `next_cursor` as `before` to get the next older page."""
        company_id = self._authorized_company_id(user)
        limit = clamp_limit(limit)
        rows = await self.maintenance_repository.list_company_tickets(
            company_id, since, until, before, limit + 1
        )
        return cap_rows(rows, limit, lambda row: Cursor(row.created_date, row.id))

    async def get_machine_history(
        self,
        user: UserModel,
        machine_id: str,
        since: date | None = None,
        until: date | None = None,
        limit: int = MAX_ROWS,
        before: Cursor | None = None,
    ) -> CappedResult[dict]:
        """A machine's tickets, newest first, capped at `limit` (max 100), each with its triggering alarm
        (if any). When truncated, pass `next_cursor` as `before` to get the next older page."""
        company_id = self._authorized_company_id(user)
        # A missing machine and another company's machine are indistinguishable on purpose.
        if await self.machine_repository.get_machine_company_id(machine_id) != company_id:
            raise AccessDeniedError(f"You cannot access machine '{machine_id}'.")
        limit = clamp_limit(limit)
        rows = await self.maintenance_repository.get_machine_history(
            machine_id, since, until, before, limit + 1
        )
        return cap_rows(rows, limit, lambda row: Cursor(row["created_date"], row["ticket_id"]))


def get_maintenance_service(db_session: AsyncSession = Depends(get_db)) -> MaintenanceService:
    return MaintenanceService(MachineRepository(db_session), MaintenanceRepository(db_session))
