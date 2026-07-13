

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CreateClientRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str

class CreateClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str