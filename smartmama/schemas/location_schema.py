from pydantic import BaseModel, Field
from uuid import UUID


class LocationBase(BaseModel):
    location_name: str = Field(..., max_length=100, description="Community name or estate where the mother resides")


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    location_name: str | None = Field(None, max_length=100, description="Community name or estate where the mother resides")


class LocationResponse(LocationBase):
    location_id: UUID
    latitude: float
    longitude: float

    class Config:
        from_attributes = True
