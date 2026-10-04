from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrderLineModel, OrderModel


class OrderRepository:
    """Every method is scoped to company_id; order lines are reached through their order."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def list_orders(self, company_id: str) -> list[OrderModel]:
        result = await self.db_session.execute(
            select(OrderModel)
            .where(OrderModel.company_id == company_id)
            .order_by(OrderModel.order_date.desc())
        )
        return list(result.scalars().all())

    async def get_order(self, order_id: str, company_id: str) -> OrderModel | None:
        result = await self.db_session.execute(
            select(OrderModel).where(OrderModel.id == order_id, OrderModel.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def list_orders_by_quote(self, quote_id: str, company_id: str) -> list[OrderModel]:
        result = await self.db_session.execute(
            select(OrderModel)
            .where(OrderModel.quote_id == quote_id, OrderModel.company_id == company_id)
            .order_by(OrderModel.order_date.asc())
        )
        return list(result.scalars().all())

    async def list_order_lines(self, order_id: str, company_id: str) -> list[OrderLineModel]:
        result = await self.db_session.execute(
            select(OrderLineModel)
            .join(OrderModel, OrderModel.id == OrderLineModel.order_id)
            .where(OrderLineModel.order_id == order_id, OrderModel.company_id == company_id)
            .order_by(OrderLineModel.id)
        )
        return list(result.scalars().all())
