from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid


class PregnancyBase(BaseModel):
    mother_id: uuid.UUID
    last_menstrual_period: Optional[datetime] = None
    expected_delivery_date: datetime
    gestational_age: int
    pregnancy_status: str

    class Config:
        from_attributes = True


class PregnancyCreate(PregnancyBase):
    pass


class PregnancyResponse(PregnancyBase):
    pregnancy_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class PregnancyUpdate(BaseModel):
    last_menstrual_period: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    gestational_age: Optional[int] = None
    pregnancy_status: Optional[str] = None

    class Config:
        from_attributes = True
