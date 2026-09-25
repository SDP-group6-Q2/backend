from fastapi import APIRouter, Depends

from app.core.auth import current_active_user
from app.models import UserModel
from app.schemas import OrderRead, QuoteLineRead, QuoteRead, QuoteRevisionRead
from app.services import (
    OrderService,
    QuoteService,
    get_order_service,
    get_quote_service,
)

router = APIRouter(dependencies=[Depends(current_active_user)])


@router.get("/", response_model=list[QuoteRead])
async def get_company_quotes(
    user: UserModel = Depends(current_active_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    return await quote_service.get_company_quotes(user)


@router.get("/revisions/{quote_revision_id}/lines", response_model=list[QuoteLineRead])
async def get_quote_lines(
    quote_revision_id: str,
    user: UserModel = Depends(current_active_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    return await quote_service.get_lines(user, quote_revision_id)


@router.get("/{quote_id}", response_model=QuoteRead)
async def get_quote(
    quote_id: str,
    user: UserModel = Depends(current_active_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    return await quote_service.get_quote(user, quote_id)


@router.get("/{quote_id}/revisions", response_model=list[QuoteRevisionRead])
async def get_quote_revisions(
    quote_id: str,
    user: UserModel = Depends(current_active_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    return await quote_service.get_revisions(user, quote_id)


@router.get("/{quote_id}/revisions/latest", response_model=QuoteRevisionRead)
async def get_latest_quote_revision(
    quote_id: str,
    user: UserModel = Depends(current_active_user),
    quote_service: QuoteService = Depends(get_quote_service),
):
    return await quote_service.get_latest_revision(user, quote_id)


@router.get("/{quote_id}/orders", response_model=list[OrderRead])
async def get_orders_by_quote(
    quote_id: str,
    user: UserModel = Depends(current_active_user),
    order_service: OrderService = Depends(get_order_service),
):
    """Orders created from this quote (empty if it never became an order)."""
    return await order_service.get_orders_by_quote(user, quote_id)
