from pydantic import BaseModel, ConfigDict, Field


class ManualRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    machine_id: str = Field(validation_alias="id")
    serial_number: str
    filename: str = Field(validation_alias="storage_path")


class ManualUrlRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    machine_id: str
    url: str
    expires_in_seconds: int
