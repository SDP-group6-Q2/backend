from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CreateClientRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str


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
