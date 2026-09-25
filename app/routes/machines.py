from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.auth import current_active_user
from app.core.pagination import MAX_ROWS, decode_cursor
from app.models import UserModel
from app.schemas import (
    AlarmRead,
    AlarmSummaryRow,
    MachineRead,
    MaintenanceHistoryRow,
    Page,
    TelemetrySnapshotRead,
    TelemetrySummaryRow,
    to_page,
)
from app.services import (
    FleetService,
    MaintenanceService,
    TelemetryService,
    get_fleet_service,
    get_maintenance_service,
    get_telemetry_service,
)

router = APIRouter(dependencies=[Depends(current_active_user)])

_Limit = Query(MAX_ROWS, ge=1, le=MAX_ROWS, description="Page size, at most 100.")
_Cursor = Query(None, description="`next_cursor` of the previous page, to fetch the next older one.")


@router.get("/", response_model=list[MachineRead])
async def get_company_machines(
    user: UserModel = Depends(current_active_user),
    fleet_service: FleetService = Depends(get_fleet_service),
):
    return await fleet_service.get_company_machines(user)


@router.get("/{machine_id}", response_model=MachineRead)
async def get_machine(
    machine_id: str,
    user: UserModel = Depends(current_active_user),
    fleet_service: FleetService = Depends(get_fleet_service),
):
    return await fleet_service.get_machine(user, machine_id)


@router.get("/{machine_id}/telemetry/latest", response_model=TelemetrySnapshotRead | None)
async def get_latest_telemetry_snapshot(
    machine_id: str,
    user: UserModel = Depends(current_active_user),
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    return await telemetry_service.get_latest_snapshot(user, machine_id)


@router.get("/{machine_id}/telemetry/summary", response_model=list[TelemetrySummaryRow])
async def get_telemetry_summary(
    machine_id: str,
    since: datetime | None = None,
    until: datetime | None = None,
    bucket: Literal["day", "week"] = "day",
    user: UserModel = Depends(current_active_user),
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    return await telemetry_service.get_telemetry_summary(user, machine_id, since, until, bucket)


@router.get("/{machine_id}/telemetry", response_model=Page[TelemetrySnapshotRead])
async def get_telemetry_history(
    machine_id: str,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = _Limit,
    cursor: str | None = _Cursor,
    user: UserModel = Depends(current_active_user),
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    """Snapshots ordered oldest to newest within a page; pages walk backwards in time."""
    result = await telemetry_service.get_telemetry_history(
        user, machine_id, since, until, limit, decode_cursor(cursor)
    )
    return to_page(result)


@router.get("/{machine_id}/alarms/summary", response_model=list[AlarmSummaryRow])
async def get_alarm_summary(
    machine_id: str,
    since: datetime | None = None,
    until: datetime | None = None,
    user: UserModel = Depends(current_active_user),
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    return await telemetry_service.get_alarm_summary(user, machine_id, since, until)


@router.get("/{machine_id}/alarms", response_model=Page[AlarmRead])
async def get_alarm_history(
    machine_id: str,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = _Limit,
    cursor: str | None = _Cursor,
    user: UserModel = Depends(current_active_user),
    telemetry_service: TelemetryService = Depends(get_telemetry_service),
):
    result = await telemetry_service.get_alarm_history(
        user, machine_id, since, until, limit, decode_cursor(cursor)
    )
    return to_page(result)


@router.get("/{machine_id}/maintenance", response_model=Page[MaintenanceHistoryRow])
async def get_machine_maintenance_history(
    machine_id: str,
    since: date | None = None,
    until: date | None = None,
    limit: int = _Limit,
    cursor: str | None = _Cursor,
    user: UserModel = Depends(current_active_user),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service),
):
    """The machine's tickets, each with the alarm that triggered it (if any)."""
    result = await maintenance_service.get_machine_history(
        user,
        machine_id,
        since,
        until,
        limit,
        decode_cursor(cursor),
    )
    return to_page(result)
