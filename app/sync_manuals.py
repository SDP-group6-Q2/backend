"""Points machines at the manual PDFs in the Supabase bucket. Safe to run multiple times.

    python -m app.sync_manuals

Run after app.seed_dataset: it matches "<serialNumber>_manual_EN.pdf" files to existing machines.
"""

import asyncio
import logging

from app.db.session import async_session_maker
from app.repositories import MachineRepository
from app.services.manual_service import ManualService
from app.storage.manual_storage import ManualStorage

logger = logging.getLogger(__name__)


async def main() -> None:
    async with async_session_maker() as session:
        result = await ManualService(MachineRepository(session), ManualStorage()).sync_storage_paths()
    logger.info("Linked %d manual(s) to machines", len(result.matched))
    for filename in result.unmatched:
        logger.warning("%s has no matching machine (by serial number)", filename)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
