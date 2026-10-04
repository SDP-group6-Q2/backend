from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class MachineModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    model_code: str
    description: str | None
    primitive_diameter: int | None
    nominal_heads: int | None
    container_type: str | None
    cap_type: str | None
    industry_segment: str | None
    notes: str | None


class MachineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    model_id: str
    serial_number: str
    delivery_date: date | None
    plant_location: str | None
    configuration_profile: str | None
    plc_family: str | None
    software_version: str | None
    model: MachineModelRead


class TelemetrySnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    timestamp: datetime
    operational_status: str
    production_rate_bph: float | None
    uptime_percentage: float | None
    alarm_count: int | None
    temperature_c: float | None
    energy_kwh: float | None
    health_note: str | None


class TelemetrySummaryRow(BaseModel):
    bucket_start: datetime
    avg_uptime_percentage: float | None
    avg_production_rate_bph: float | None
    total_alarm_count: int | None
    min_temperature_c: float | None
    max_temperature_c: float | None
    avg_energy_kwh: float | None
    snapshot_count: int


class AlarmRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    machine_id: str
    timestamp: datetime
    alarm_code: str
    severity: str
    alarm_status: str


class AlarmSummaryRow(BaseModel):
    alarm_code: str
    severity: str
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    open_count: int


class MaintenanceTicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(validation_alias=AliasChoices("id", "ticket_id"))
    machine_id: str
    alarm_id: str | None
    ticket_type: str
    ticket_status: str
    priority: str
    created_date: date
    owner_role: str | None


class MaintenanceHistoryRow(MaintenanceTicketRead):
    """A machine's ticket joined with the alarm that triggered it (all alarm_* fields are null
    for tickets that didn't originate from an alarm)."""

    alarm_code: str | None
    severity: str | None
    alarm_status: str | None
    alarm_timestamp: datetime | None
