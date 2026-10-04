from collections import defaultdict

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AccessDeniedError, NotFoundError
from app.db.session import get_db
from app.models import QuoteLineModel, QuoteModel, QuoteRevisionModel, UserModel
from app.repositories import OrderRepository, QuoteRepository
from app.schemas import QuoteOverviewRow

# Quotes, revisions and lines are commercial data: commercial/full only.
_COMMERCIAL_VISIBILITIES = {"full", "commercial"}

# (revision, line count, net total), a quote's revisions in revision-number order.
RevisionTotals = tuple[QuoteRevisionModel, int, float | None]


def revisions_by_quote(rows: list[RevisionTotals]) -> dict[str, list[RevisionTotals]]:
    grouped: dict[str, list[RevisionTotals]] = defaultdict(list)
    for row in rows:
        grouped[row[0].quote_id].append(row)
    return grouped


def approved_revision(revisions: list[RevisionTotals]) -> RevisionTotals | None:
    """The revision an order is made from: the highest-numbered Approved one."""
    approved = [row for row in revisions if row[0].revision_status == "Approved"]
    return approved[-1] if approved else None


def rounded(total: float | None) -> float | None:
    return None if total is None else round(total, 2)


class QuoteService:
    """Quotes have no status column: lifecycle lives on the revision, and the highest
    revision_number is the current one. Line prices are already net of the revision's
    discount_rate, so nothing here applies it again."""

    def __init__(self, quote_repository: QuoteRepository, order_repository: OrderRepository):
        self.quote_repository = quote_repository
        self.order_repository = order_repository

    @staticmethod
    def _authorized_company_id(user: UserModel) -> str:
        company_id = user.client.company_id if user.client else None
        if company_id is None or user.visibility not in _COMMERCIAL_VISIBILITIES:
            raise AccessDeniedError("You cannot access commercial information.")
        return company_id

    async def get_company_quotes(self, user: UserModel) -> list[QuoteModel]:
        return await self.quote_repository.list_quotes(self._authorized_company_id(user))

    async def get_quotes_overview(self, user: UserModel) -> list[QuoteOverviewRow]:
        """Every quote, newest first, with its latest revision's status, line count and net total and the orders
        made from it: what a listing or a total over quotes needs, in one call."""
        company_id = self._authorized_company_id(user)
        quotes = await self.quote_repository.list_quotes(company_id)
        revisions = revisions_by_quote(await self.quote_repository.list_revision_totals(company_id))
        order_ids: dict[str, list[str]] = defaultdict(list)
        for order in reversed(await self.order_repository.list_orders(company_id)):  # oldest first
            if order.quote_id:
                order_ids[order.quote_id].append(order.id)
        rows = []
        for quote in quotes:
            latest = revisions[quote.id][-1] if revisions.get(quote.id) else None
            revision, line_count, total = latest if latest else (None, 0, None)
            rows.append(
                QuoteOverviewRow(
                    id=quote.id,
                    currency=quote.currency,
                    created_at=quote.created_at,
                    valid_until=quote.valid_until,
                    description=quote.description,
                    latest_revision_id=revision.id if revision else None,
                    latest_revision_number=revision.revision_number if revision else None,
                    status=revision.revision_status if revision else None,
                    discount_rate=revision.discount_rate if revision else None,
                    line_count=line_count,
                    net_total=rounded(total),
                    order_ids=order_ids.get(quote.id, []),
                )
            )
        return rows

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
    return QuoteService(QuoteRepository(db_session), OrderRepository(db_session))
