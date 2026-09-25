from datetime import datetime
from typing import Literal

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccessDeniedError
from app.db.session import get_db
from app.core.pagination import MAX_ROWS, CappedResult, Cursor, cap_rows, clamp_limit
from app.models import AlarmModel, TelemetrySnapshotModel, UserModel
from app.repositories import AlarmRepository, MachineRepository, TelemetryRepository

# Telemetry and alarms are operational data: technician/full only.
_OPERATIONAL_VISIBILITIES = {"full", "technician"}


class TelemetryService:
    """Telemetry snapshots and alarms of a machine, for operational-tier users of the owning company."""

    def __init__(
        self,
        machine_repository: MachineRepository,
        telemetry_repository: TelemetryRepository,
        alarm_repository: AlarmRepository,
    ):
        self.machine_repository = machine_repository
        self.telemetry_repository = telemetry_repository
        self.alarm_repository = alarm_repository

    async def _require_machine_access(self, user: UserModel, machine_id: str) -> None:
        company_id = user.client.company_id if user.client else None
        if company_id is None or user.visibility not in _OPERATIONAL_VISIBILITIES:
            raise AccessDeniedError("You cannot access operational data.")
        # A missing machine and another company's machine are indistinguishable on purpose.
        if await self.machine_repository.get_machine_company_id(machine_id) != company_id:
            raise AccessDeniedError(f"You cannot access machine '{machine_id}'.")

    async def get_latest_snapshot(self, user: UserModel, machine_id: str) -> TelemetrySnapshotModel | None:
        await self._require_machine_access(user, machine_id)
        return await self.telemetry_repository.get_latest_snapshot(machine_id)

    async def get_telemetry_summary(
        self,
        user: UserModel,
        machine_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        bucket: Literal["day", "week"] = "day",
    ) -> list[dict]:
        """Per-day/week aggregates: the compact alternative to raw hourly history for trend questions."""
        await self._require_machine_access(user, machine_id)
        return await self.telemetry_repository.get_summary(machine_id, since, until, bucket)

    async def get_telemetry_history(
        self,
        user: UserModel,
        machine_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = MAX_ROWS,
        before: Cursor | None = None,
    ) -> CappedResult[TelemetrySnapshotModel]:
        """The most recent snapshots in range, capped at `limit` (max 100), returned oldest to newest.
        When truncated, pass `next_cursor` as `before` to get the next older page."""
        await self._require_machine_access(user, machine_id)
        limit = clamp_limit(limit)
        rows = await self.telemetry_repository.get_history(machine_id, since, until, before, limit + 1)
        capped = cap_rows(rows, limit, lambda row: Cursor(row.timestamp, row.id))
        capped.rows.reverse()
        return capped

    async def get_alarm_summary(
        self,
        user: UserModel,
        machine_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[dict]:
        """Alarm counts grouped by code and severity, for "why does this keep alarming" questions."""
        await self._require_machine_access(user, machine_id)
        return await self.alarm_repository.get_summary(machine_id, since, until)

    async def get_alarm_history(
        self,
        user: UserModel,
        machine_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = MAX_ROWS,
        before: Cursor | None = None,
    ) -> CappedResult[AlarmModel]:
        """The most recent alarms in range, newest first, capped at `limit` (max 100).
        When truncated, pass `next_cursor` as `before` to get the next older page."""
        await self._require_machine_access(user, machine_id)
        limit = clamp_limit(limit)
        rows = await self.alarm_repository.get_history(machine_id, since, until, before, limit + 1)
        return cap_rows(rows, limit, lambda row: Cursor(row.timestamp, row.id))


def get_telemetry_service(db_session: AsyncSession = Depends(get_db)) -> TelemetryService:
    return TelemetryService(
        MachineRepository(db_session), TelemetryRepository(db_session), AlarmRepository(db_session)
    )
