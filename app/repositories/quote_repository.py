from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QuoteLineModel, QuoteModel, QuoteRevisionModel


class QuoteRepository:
    """Every method is scoped to company_id; revisions and lines are reached through their quote."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def list_quotes(self, company_id: str) -> list[QuoteModel]:
        result = await self.db_session.execute(
            select(QuoteModel)
            .where(QuoteModel.company_id == company_id)
            .order_by(QuoteModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_quote(self, quote_id: str, company_id: str) -> QuoteModel | None:
        result = await self.db_session.execute(
            select(QuoteModel).where(QuoteModel.id == quote_id, QuoteModel.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def list_revisions(self, quote_id: str, company_id: str) -> list[QuoteRevisionModel]:
        result = await self.db_session.execute(
            select(QuoteRevisionModel)
            .join(QuoteModel, QuoteModel.id == QuoteRevisionModel.quote_id)
            .where(QuoteRevisionModel.quote_id == quote_id, QuoteModel.company_id == company_id)
            .order_by(QuoteRevisionModel.revision_number.asc())
        )
        return list(result.scalars().all())

    async def get_latest_revision(self, quote_id: str, company_id: str) -> QuoteRevisionModel | None:
        result = await self.db_session.execute(
            select(QuoteRevisionModel)
            .join(QuoteModel, QuoteModel.id == QuoteRevisionModel.quote_id)
            .where(QuoteRevisionModel.quote_id == quote_id, QuoteModel.company_id == company_id)
            .order_by(QuoteRevisionModel.revision_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_lines(self, quote_revision_id: str, company_id: str) -> list[QuoteLineModel]:
        result = await self.db_session.execute(
            select(QuoteLineModel)
            .join(QuoteRevisionModel, QuoteRevisionModel.id == QuoteLineModel.quote_revision_id)
            .join(QuoteModel, QuoteModel.id == QuoteRevisionModel.quote_id)
            .where(
                QuoteLineModel.quote_revision_id == quote_revision_id,
                QuoteModel.company_id == company_id,
            )
            .order_by(QuoteLineModel.id)
        )
        return list(result.scalars().all())
