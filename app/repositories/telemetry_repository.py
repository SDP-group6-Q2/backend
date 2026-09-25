from datetime import datetime
from typing import Literal

from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.pagination import Cursor
from app.models import TelemetrySnapshotModel

Bucket = Literal["day", "week"]


class TelemetryRepository:
    """Machine-scoped only: callers must have verified the machine's ownership."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @staticmethod
    def _in_range(query: Select, since: datetime | None, until: datetime | None) -> Select:
        if since is not None:
            query = query.where(TelemetrySnapshotModel.timestamp >= since)
        if until is not None:
            query = query.where(TelemetrySnapshotModel.timestamp <= until)
        return query

    async def get_latest_snapshot(self, machine_id: str) -> TelemetrySnapshotModel | None:
        result = await self.db_session.execute(
            select(TelemetrySnapshotModel)
            .where(TelemetrySnapshotModel.machine_id == machine_id)
            .order_by(TelemetrySnapshotModel.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        machine_id: str,
        since: datetime | None,
        until: datetime | None,
        before: Cursor | None,
        limit: int,
    ) -> list[TelemetrySnapshotModel]:
        """Newest first; `before` restricts to rows strictly older than that cursor."""
        query = self._in_range(
            select(TelemetrySnapshotModel).where(TelemetrySnapshotModel.machine_id == machine_id),
            since,
            until,
        )
        if before is not None:
            query = query.where(
                tuple_(TelemetrySnapshotModel.timestamp, TelemetrySnapshotModel.id)
                < tuple_(before.sort_key, before.id)
            )
        result = await self.db_session.execute(
            query.order_by(TelemetrySnapshotModel.timestamp.desc(), TelemetrySnapshotModel.id.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_summary(
        self, machine_id: str, since: datetime | None, until: datetime | None, bucket: Bucket
    ) -> list[dict]:
        bucket_start = func.date_trunc(bucket, TelemetrySnapshotModel.timestamp).label("bucket_start")
        query = self._in_range(
            select(
                bucket_start,
                func.avg(TelemetrySnapshotModel.uptime_percentage).label("avg_uptime_percentage"),
                func.avg(TelemetrySnapshotModel.production_rate_bph).label("avg_production_rate_bph"),
                func.sum(TelemetrySnapshotModel.alarm_count).label("total_alarm_count"),
                func.min(TelemetrySnapshotModel.temperature_c).label("min_temperature_c"),
                func.max(TelemetrySnapshotModel.temperature_c).label("max_temperature_c"),
                func.avg(TelemetrySnapshotModel.energy_kwh).label("avg_energy_kwh"),
                func.count().label("snapshot_count"),
            ).where(TelemetrySnapshotModel.machine_id == machine_id),
            since,
            until,
        )
        result = await self.db_session.execute(query.group_by(bucket_start).order_by(bucket_start.asc()))
        return [dict(row) for row in result.mappings().all()]
