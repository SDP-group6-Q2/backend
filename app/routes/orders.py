from fastapi import APIRouter, Depends

from app.core.auth import current_active_user
from app.models import UserModel
from app.schemas import OrderLineRead, OrderOverviewRow, OrderRead
from app.services import OrderService, get_order_service

router = APIRouter(dependencies=[Depends(current_active_user)])


@router.get("/", response_model=list[OrderRead])
async def get_company_orders(
    user: UserModel = Depends(current_active_user),
    order_service: OrderService = Depends(get_order_service),
):
    """Newest first."""
    return await order_service.get_company_orders(user)


@router.get("/overview", response_model=list[OrderOverviewRow])
async def get_orders_overview(
    user: UserModel = Depends(current_active_user),
    order_service: OrderService = Depends(get_order_service),
):
    """Newest first, each order with the line count and net total of its quote's approved revision."""
    return await order_service.get_orders_overview(user)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: str,
    user: UserModel = Depends(current_active_user),
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_order(user, order_id)


@router.get("/{order_id}/lines", response_model=list[OrderLineRead])
async def get_order_lines(
    order_id: str,
    user: UserModel = Depends(current_active_user),
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_order_lines(user, order_id)
