from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AccessDeniedError, NotFoundError
from app.db.session import get_db
from app.models import MachineModel, UserModel
from app.repositories import MachineRepository
from app.storage.manual_storage import ManualStorage

# Manuals are machine documentation: visible to every tier, for the user's own company's machines.
_MACHINE_IDENTITY_VISIBILITIES = {"full", "technician", "commercial"}

_MANUAL_FILENAME_SUFFIX = "_manual_EN.pdf"


@dataclass
class ManualUrl:
    machine_id: str
    url: str
    expires_in_seconds: int


@dataclass
class ManualSyncResult:
    matched: list[str]
    unmatched: list[str]


class ManualService:
    def __init__(self, machine_repository: MachineRepository, storage: ManualStorage):
        self.machine_repository = machine_repository
        self.storage = storage

    @staticmethod
    def _authorized_company_id(user: UserModel) -> str:
        company_id = user.client.company_id if user.client else None
        if company_id is None or user.visibility not in _MACHINE_IDENTITY_VISIBILITIES:
            raise AccessDeniedError("You cannot access machine documentation.")
        return company_id

    async def list_manuals(self, user: UserModel) -> list[MachineModel]:
        """The user's company's machines that have a manual on file."""
        company_id = self._authorized_company_id(user)
        return await self.machine_repository.list_machines_with_manual(company_id)

    async def get_manual_url(self, user: UserModel, machine_id: str) -> ManualUrl:
        company_id = self._authorized_company_id(user)
        machine = await self.machine_repository.get_machine(machine_id, company_id)
        # Unknown machine, another company's machine and a machine with no manual look the same.
        if machine is None or machine.storage_path is None:
            raise NotFoundError(f"No manual available for machine '{machine_id}'.")
        url = await self.storage.create_signed_url(machine.storage_path)
        return ManualUrl(machine.id, url, settings.manual_url_ttl_seconds)

    async def sync_storage_paths(self) -> ManualSyncResult:
        """Point machines at the manual PDFs currently in the bucket. Each file is named
        "<serialNumber>_manual_EN.pdf", so the serial number is the join key. Idempotent."""
        matched, unmatched = [], []
        for filename in await self.storage.list_filenames():
            if not filename.endswith(_MANUAL_FILENAME_SUFFIX):
                continue
            serial_number = filename[: -len(_MANUAL_FILENAME_SUFFIX)]
            count = await self.machine_repository.set_storage_path_by_serial(serial_number, filename)
            (matched if count else unmatched).append(filename)
        return ManualSyncResult(matched, unmatched)


def get_manual_service(db_session: AsyncSession = Depends(get_db)) -> ManualService:
    return ManualService(MachineRepository(db_session), ManualStorage())
