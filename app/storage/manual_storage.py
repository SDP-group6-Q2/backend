"""Supabase Storage access for the manuals PDF bucket.

The PDF bytes live in Supabase Storage, not in Postgres: `machine.storage_path` only maps a
machine to its object key. This is the one place that talks to Supabase, and it knows nothing
about users: callers must run their own access check (see ManualService) before asking for a
signed URL.

The supabase client is synchronous, so calls run in a worker thread.
"""

import asyncio

from supabase import Client, create_client

from app.core.config import settings
from app.core.exceptions import StorageUnavailableError


class ManualStorage:
    def __init__(self) -> None:
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is None:
            if not settings.supabase_url or not settings.supabase_service_role_key:
                raise StorageUnavailableError("Document storage is not configured.")
            self._client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        return self._client

    def _create_signed_url(self, storage_path: str) -> str:
        bucket = self._get_client().storage.from_(settings.manuals_bucket)
        return bucket.create_signed_url(storage_path, settings.manual_url_ttl_seconds)["signedURL"]

    def _list_filenames(self) -> list[str]:
        entries = self._get_client().storage.from_(settings.manuals_bucket).list()
        return [entry["name"] for entry in entries]

    async def create_signed_url(self, storage_path: str) -> str:
        """Short-lived URL for one object. The caller must already have authorized the request."""
        try:
            return await asyncio.to_thread(self._create_signed_url, storage_path)
        except StorageUnavailableError:
            raise
        except Exception as e:
            raise StorageUnavailableError(f"Could not sign the manual URL: {e!r}") from e

    async def list_filenames(self) -> list[str]:
        try:
            return await asyncio.to_thread(self._list_filenames)
        except StorageUnavailableError:
            raise
        except Exception as e:
            raise StorageUnavailableError(f"Could not list the manuals bucket: {e!r}") from e
