from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CreateClientRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    # Bridge key into mcp-server's fleet dataset (assistant.companies.companyid),
    # validated in app/routes/clients.py before creation. country/sector/city/
    # currency/locale are auto-filled from that lookup, not accepted here.
    company_id: str


class CreateClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    company_id: str | None = None
    country: str | None = None
    sector: str | None = None
    city: str | None = None
    currency: str | None = None
    locale: str | None = None
