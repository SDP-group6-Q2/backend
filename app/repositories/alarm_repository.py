from datetime import datetime

from sqlalchemy import case, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.pagination import Cursor
from app.models import AlarmModel


class AlarmRepository:
    """Machine-scoped only: callers must have verified the machine's ownership."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @staticmethod
    def _in_range(query: Select, since: datetime | None, until: datetime | None) -> Select:
        if since is not None:
            query = query.where(AlarmModel.timestamp >= since)
        if until is not None:
            query = query.where(AlarmModel.timestamp <= until)
        return query

    async def get_history(
        self,
        machine_id: str,
        since: datetime | None,
        until: datetime | None,
        before: Cursor | None,
        limit: int,
    ) -> list[AlarmModel]:
        """Newest first; `before` restricts to rows strictly older than that cursor."""
        query = self._in_range(select(AlarmModel).where(AlarmModel.machine_id == machine_id), since, until)
        if before is not None:
            query = query.where(
                tuple_(AlarmModel.timestamp, AlarmModel.id) < tuple_(before.sort_key, before.id)
            )
        result = await self.db_session.execute(
            query.order_by(AlarmModel.timestamp.desc(), AlarmModel.id.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_summary(
        self, machine_id: str, since: datetime | None, until: datetime | None
    ) -> list[dict]:
        occurrence_count = func.count().label("occurrence_count")
        query = self._in_range(
            select(
                AlarmModel.alarm_code,
                AlarmModel.severity,
                occurrence_count,
                func.min(AlarmModel.timestamp).label("first_seen"),
                func.max(AlarmModel.timestamp).label("last_seen"),
                func.sum(case((AlarmModel.alarm_status == "Open", 1), else_=0)).label("open_count"),
            ).where(AlarmModel.machine_id == machine_id),
            since,
            until,
        )
        result = await self.db_session.execute(
            query.group_by(AlarmModel.alarm_code, AlarmModel.severity).order_by(occurrence_count.desc())
        )
        return [dict(row) for row in result.mappings().all()]
