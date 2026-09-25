from datetime import date

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import Select

from app.core.pagination import Cursor
from app.models import AlarmModel, MachineModel, MaintenanceTicketModel


class MaintenanceRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @staticmethod
    def _in_range(
        query: Select, since: date | None, until: date | None, before: Cursor | None
    ) -> Select:
        if since is not None:
            query = query.where(MaintenanceTicketModel.created_date >= since)
        if until is not None:
            query = query.where(MaintenanceTicketModel.created_date <= until)
        if before is not None:
            query = query.where(
                tuple_(MaintenanceTicketModel.created_date, MaintenanceTicketModel.id)
                < tuple_(before.sort_key, before.id)
            )
        return query

    async def list_company_tickets(
        self,
        company_id: str,
        since: date | None,
        until: date | None,
        before: Cursor | None,
        limit: int,
    ) -> list[MaintenanceTicketModel]:
        """Tickets of the company's machines, newest first; `before` restricts to strictly older rows."""
        query = self._in_range(
            select(MaintenanceTicketModel)
            .join(MachineModel, MachineModel.id == MaintenanceTicketModel.machine_id)
            .where(MachineModel.company_id == company_id),
            since,
            until,
            before,
        )
        result = await self.db_session.execute(
            query.order_by(MaintenanceTicketModel.created_date.desc(), MaintenanceTicketModel.id.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_machine_history(
        self,
        machine_id: str,
        since: date | None,
        until: date | None,
        before: Cursor | None,
        limit: int,
    ) -> list[dict]:
        """A machine's tickets, newest first, each with the alarm that triggered it (LEFT JOIN:
        tickets that didn't originate from an alarm are kept)."""
        alarm = aliased(AlarmModel)
        query = self._in_range(
            select(
                MaintenanceTicketModel.id.label("ticket_id"),
                MaintenanceTicketModel.machine_id,
                MaintenanceTicketModel.alarm_id,
                MaintenanceTicketModel.ticket_type,
                MaintenanceTicketModel.ticket_status,
                MaintenanceTicketModel.priority,
                MaintenanceTicketModel.created_date,
                MaintenanceTicketModel.owner_role,
                alarm.alarm_code,
                alarm.severity,
                alarm.alarm_status,
                alarm.timestamp.label("alarm_timestamp"),
            )
            .select_from(MaintenanceTicketModel)
            .outerjoin(alarm, alarm.id == MaintenanceTicketModel.alarm_id)
            .where(MaintenanceTicketModel.machine_id == machine_id),
            since,
            until,
            before,
        )
        result = await self.db_session.execute(
            query.order_by(MaintenanceTicketModel.created_date.desc(), MaintenanceTicketModel.id.desc()).limit(limit)
        )
        return [dict(row) for row in result.mappings().all()]
