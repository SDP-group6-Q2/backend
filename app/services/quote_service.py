from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccessDeniedError, NotFoundError
from app.db.session import get_db
from app.models import QuoteLineModel, QuoteModel, QuoteRevisionModel, UserModel
from app.repositories import QuoteRepository

# Quotes, revisions and lines are commercial data: commercial/full only.
_COMMERCIAL_VISIBILITIES = {"full", "commercial"}


class QuoteService:
    """Quotes have no status column: lifecycle lives on the revision, and the highest
    revision_number is the current one. Line prices are already net of the revision's
    discount_rate, so nothing here applies it again."""

    def __init__(self, quote_repository: QuoteRepository):
        self.quote_repository = quote_repository

    @staticmethod
    def _authorized_company_id(user: UserModel) -> str:
        company_id = user.client.company_id if user.client else None
        if company_id is None or user.visibility not in _COMMERCIAL_VISIBILITIES:
            raise AccessDeniedError("You cannot access commercial information.")
        return company_id

    async def get_company_quotes(self, user: UserModel) -> list[QuoteModel]:
        return await self.quote_repository.list_quotes(self._authorized_company_id(user))

    async def get_quote(self, user: UserModel, quote_id: str) -> QuoteModel:
        quote = await self.quote_repository.get_quote(quote_id, self._authorized_company_id(user))
        if quote is None:
            raise NotFoundError(f"Quote '{quote_id}' not found.")
        return quote

    async def get_revisions(self, user: UserModel, quote_id: str) -> list[QuoteRevisionModel]:
        """All revisions of a quote, oldest first."""
        company_id = self._authorized_company_id(user)
        if await self.quote_repository.get_quote(quote_id, company_id) is None:
            raise NotFoundError(f"Quote '{quote_id}' not found.")
        return await self.quote_repository.list_revisions(quote_id, company_id)

    async def get_latest_revision(self, user: UserModel, quote_id: str) -> QuoteRevisionModel:
        company_id = self._authorized_company_id(user)
        revision = await self.quote_repository.get_latest_revision(quote_id, company_id)
        if revision is None:
            raise NotFoundError(f"Quote '{quote_id}' not found.")
        return revision

    async def get_lines(self, user: UserModel, quote_revision_id: str) -> list[QuoteLineModel]:
        """Lines of one revision. machine_id is empty on lines that don't refer to an installed machine."""
        return await self.quote_repository.list_lines(
            quote_revision_id, self._authorized_company_id(user)
        )


def get_quote_service(db_session: AsyncSession = Depends(get_db)) -> QuoteService:
    return QuoteService(QuoteRepository(db_session))
