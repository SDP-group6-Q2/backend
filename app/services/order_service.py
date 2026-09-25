from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccessDeniedError, NotFoundError
from app.db.session import get_db
from app.models import OrderLineModel, OrderModel, UserModel
from app.repositories import OrderRepository

# Orders and order lines are commercial data: commercial/full only.
_COMMERCIAL_VISIBILITIES = {"full", "commercial"}


class OrderService:
    """Order lines track fulfilment only: an order's content comes from the quote lines of its
    approved revision."""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    @staticmethod
    def _authorized_company_id(user: UserModel) -> str:
        company_id = user.client.company_id if user.client else None
        if company_id is None or user.visibility not in _COMMERCIAL_VISIBILITIES:
            raise AccessDeniedError("You cannot access commercial information.")
        return company_id

    async def get_company_orders(self, user: UserModel) -> list[OrderModel]:
        """Newest first."""
        return await self.order_repository.list_orders(self._authorized_company_id(user))

    async def get_order(self, user: UserModel, order_id: str) -> OrderModel:
        order = await self.order_repository.get_order(order_id, self._authorized_company_id(user))
        if order is None:
            raise NotFoundError(f"Order '{order_id}' not found.")
        return order

    async def get_orders_by_quote(self, user: UserModel, quote_id: str) -> list[OrderModel]:
        """Orders created from a quote, oldest first (empty if the quote never became an order)."""
        return await self.order_repository.list_orders_by_quote(
            quote_id, self._authorized_company_id(user)
        )

    async def get_order_lines(self, user: UserModel, order_id: str) -> list[OrderLineModel]:
        return await self.order_repository.list_order_lines(
            order_id, self._authorized_company_id(user)
        )


def get_order_service(db_session: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(OrderRepository(db_session))
