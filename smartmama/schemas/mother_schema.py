from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class MotherCreate(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    date_of_birth: date
    pin: str
    location_name: str
    consent_given: bool


class MotherUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    date_of_birth: date | None = None
    pin: str | None = None
    consent_given: bool | None = None

class PersonData(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    first_name: str
    last_name: str
    phone_number: str | None = None

class MotherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mother_id: UUID
    person: PersonData
    date_of_birth: date
    location_name: str | None = None
    consent_given: bool
    created_at: datetime
    updated_at: datetime
