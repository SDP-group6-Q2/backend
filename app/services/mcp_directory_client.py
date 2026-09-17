"""Thin client for mcp-server's internal admin/service surface
(mcp-server/app/internal_api.py) -- used only for backend's own
provisioning-time validation of user_id/company_id against the fleet
dataset. Not related to the assistant chat flow: an end-user's own
visibility is fetched live via the existing gateway/JWT/get_user_visibility
MCP path (see AssistantService), never through this module.
"""

from __future__ import annotations

import httpx

from app.core.config import settings


async def lookup_user(user_id: str) -> dict | None:
    """Return {"company_id": ..., "visibility": ...} for a fleet user_id, or
    None if it doesn't exist in the assistant dataset."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.mcp_server_url}/internal/users/{user_id}",
            headers={"X-Internal-Secret": settings.internal_service_secret},
        )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


async def lookup_company(company_id: str) -> dict | None:
    """Return {"company_id", "name", "country", "sector", "city", "currency",
    "locale"} for a fleet company_id, or None if it doesn't exist."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.mcp_server_url}/internal/companies/{company_id}",
            headers={"X-Internal-Secret": settings.internal_service_secret},
        )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()
