from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.auth import current_active_user
from app.core.pagination import MAX_ROWS, decode_cursor
from app.models import UserModel
from app.schemas import MaintenanceTicketRead, Page, to_page
from app.services import MaintenanceService, get_maintenance_service

router = APIRouter(dependencies=[Depends(current_active_user)])


@router.get("/", response_model=Page[MaintenanceTicketRead])
async def get_company_maintenance_tickets(
    since: date | None = None,
    until: date | None = None,
    limit: int = Query(MAX_ROWS, ge=1, le=MAX_ROWS, description="Page size, at most 100."),
    cursor: str | None = Query(None, description="`next_cursor` of the previous page."),
    user: UserModel = Depends(current_active_user),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service),
):
    """Tickets of the company's machines, newest first. `since`/`until` match the creation date."""
    result = await maintenance_service.get_company_tickets(
        user, since, until, limit, decode_cursor(cursor)
    )
    return to_page(result)
