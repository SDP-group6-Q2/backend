"""Loads the AROL fleet dataset (xlsx) into the API's tables. Safe to run multiple times.

    python -m app.seed_dataset [--path /path/to/AROL_Q2_synthetic_fleet_dataset.xlsx]

Rows are upserted in foreign-key order. Companies are upserted into `client` by company_id.
The dataset's Users sheet is not loaded: API users register on their own and carry their
own client and visibility.
"""

import argparse
import asyncio
import logging
from datetime import date, datetime
from typing import Any

import openpyxl
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import async_session_maker
from app.models import (
    AlarmModel,
    ClientModel,
    MachineModel,
    MachineModelModel,
    MaintenanceTicketModel,
    OrderLineModel,
    OrderModel,
    QuoteLineModel,
    QuoteModel,
    QuoteRevisionModel,
    TelemetrySnapshotModel,
)

logger = logging.getLogger(__name__)

_BATCH_SIZE = 1000


def _date(value: Any) -> date | None:
    if value is None or isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def _datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _rows(workbook: openpyxl.Workbook, sheet: str) -> list[dict[str, Any]]:
    rows = workbook[sheet].iter_rows(values_only=True)
    header = next(rows)
    return [dict(zip(header, row)) for row in rows if any(value is not None for value in row)]


async def _upsert(session: AsyncSession, model: type, rows: list[dict[str, Any]], key: str) -> None:
    """INSERT ... ON CONFLICT (key) DO UPDATE. `key` is the model attribute name of the primary
    key; row dicts are keyed by column name."""
    if not rows:
        return
    key_column = model.__table__.c[getattr(model, key).property.columns[0].name]
    for start in range(0, len(rows), _BATCH_SIZE):
        batch = rows[start : start + _BATCH_SIZE]
        statement = insert(model.__table__).values(batch)
        update = {c.name: statement.excluded[c.name] for c in model.__table__.c if c is not key_column}
        await session.execute(statement.on_conflict_do_update(index_elements=[key_column], set_=update))


async def _seed_companies(session: AsyncSession, workbook: openpyxl.Workbook) -> None:
    for row in _rows(workbook, "Companies"):
        client = (
            await session.execute(select(ClientModel).where(ClientModel.company_id == row["companyId"]))
        ).scalar_one_or_none()
        if client is None:
            # Adopt a pre-existing client of the same name (e.g. created before seeding) instead of duplicating it.
            client = (
                await session.execute(select(ClientModel).where(ClientModel.name == row["companyName"]))
            ).scalar_one_or_none() or ClientModel(name=row["companyName"])
            session.add(client)
        client.company_id = row["companyId"]
        client.name = row["companyName"]
        client.country = row["country"]
        client.sector = row["sector"]
        client.city = row["city"]
        client.currency = row["currency"]
        client.locale = row["locale"]
    await session.flush()


async def seed(path: str) -> None:
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    async with async_session_maker() as session:
        await _seed_companies(session, workbook)

        await _upsert(
            session,
            MachineModelModel,
            [
                {
                    "model_id": r["modelId"],
                    "model_code": r["modelCode"],
                    "description": r["description"],
                    "primitive_diameter": r["primitiveDiameter"],
                    "nominal_heads": r["nominalHeads"],
                    "container_type": r["containerType"],
                    "cap_type": r["capType"],
                    "industry_segment": r["industrySegment"],
                    "notes": r["notes"],
                }
                for r in _rows(workbook, "MachineModels")
            ],
            "id",
        )
        await _upsert(
            session,
            MachineModel,
            [
                {
                    "machine_id": r["machineId"],
                    "company_id": r["companyId"],
                    "model_id": r["modelId"],
                    "serial_number": str(r["serialNumber"]),
                    "delivery_date": _date(r["deliveryDate"]),
                    "plant_location": r["plantLocation"],
                    "configuration_profile": r["configurationProfile"],
                    "plc_family": r["plcFamily"],
                    "software_version": None if r["softwareVersion"] is None else str(r["softwareVersion"]),
                }
                for r in _rows(workbook, "Machines")
            ],
            "id",
        )
        await _upsert(
            session,
            QuoteModel,
            [
                {
                    "quote_id": r["quoteId"],
                    "company_id": r["companyId"],
                    "currency": r["currency"],
                    "created_at": _date(r["createdAt"]),
                    "valid_until": _date(r["validUntil"]),
                    "description": r["description"],
                }
                for r in _rows(workbook, "Quotes")
            ],
            "id",
        )
        await _upsert(
            session,
            QuoteRevisionModel,
            [
                {
                    "quote_revision_id": r["quoteRevisionId"],
                    "quote_id": r["quoteId"],
                    "revision_number": r["revisionNumber"],
                    "revision_status": r["revisionStatus"],
                    "issued_at": _date(r["issuedAt"]),
                    "discount_rate": r["discountRate"],
                    "change_summary": r["changeSummary"],
                }
                for r in _rows(workbook, "QuoteRevisions")
            ],
            "id",
        )
        await _upsert(
            session,
            QuoteLineModel,
            [
                {
                    "quote_line_id": r["quoteLineId"],
                    "quote_revision_id": r["quoteRevisionId"],
                    "machine_id": r["machineId"],
                    "price": r["price"],
                    "description": r["description"],
                }
                for r in _rows(workbook, "QuoteLines")
            ],
            "id",
        )
        await _upsert(
            session,
            OrderModel,
            [
                {
                    "order_id": r["orderId"],
                    "quote_id": r["quoteId"],
                    "company_id": r["companyId"],
                    "order_status": r["orderStatus"],
                    "order_date": _date(r["orderDate"]),
                    "expected_delivery_date": _date(r["expectedDeliveryDate"]),
                    "shipment_status": r["shipmentStatus"],
                    "currency": r["currency"],
                    "notes": r["notes"],
                }
                for r in _rows(workbook, "Orders")
            ],
            "id",
        )
        await _upsert(
            session,
            OrderLineModel,
            [
                {
                    "order_line_id": r["orderLineId"],
                    "order_id": r["orderId"],
                    "fulfillment_status": r["fulfillmentStatus"],
                }
                for r in _rows(workbook, "OrderLines")
            ],
            "id",
        )
        await _upsert(
            session,
            TelemetrySnapshotModel,
            [
                {
                    "telemetry_id": r["telemetryId"],
                    "machine_id": r["machineId"],
                    "timestamp": _datetime(r["timestamp"]),
                    "operational_status": r["operationalStatus"],
                    "production_rate_bph": r["productionRateBph"],
                    "uptime_percentage": r["uptimePercentage"],
                    "alarm_count": r["alarmCount"],
                    "temperature_c": r["temperatureC"],
                    "energy_kwh": r["energyKwh"],
                    "health_note": r["healthNote"],
                }
                for r in _rows(workbook, "TelemetrySnapshots")
            ],
            "id",
        )
        await _upsert(
            session,
            AlarmModel,
            [
                {
                    "alarm_id": r["alarmId"],
                    "machine_id": r["machineId"],
                    "timestamp": _datetime(r["timestamp"]),
                    "alarm_code": r["alarmCode"],
                    "severity": r["severity"],
                    "alarm_status": r["alarmStatus"],
                }
                for r in _rows(workbook, "Alarms")
            ],
            "id",
        )
        await _upsert(
            session,
            MaintenanceTicketModel,
            [
                {
                    "ticket_id": r["ticketId"],
                    "machine_id": r["machineId"],
                    "alarm_id": r["alarmId"],
                    "ticket_type": r["ticketType"],
                    "ticket_status": r["ticketStatus"],
                    "priority": r["priority"],
                    "created_date": _date(r["createdDate"]),
                    "owner_role": r["ownerRole"],
                }
                for r in _rows(workbook, "MaintenanceTickets")
            ],
            "id",
        )
        await session.commit()
    logger.info("Dataset loaded from %s", path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Load the AROL fleet dataset into the database.")
    parser.add_argument("--path", default=settings.dataset_path, help="Path to the dataset xlsx.")
    asyncio.run(seed(parser.parse_args().path))
