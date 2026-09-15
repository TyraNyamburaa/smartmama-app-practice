from uuid import UUID
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Symptom(str, Enum):
    BLEEDING = "Bleeding"
    HEADACHE = "Headache"
    SWELLING = "Swelling"

class LoggedSymptoms(BaseModel):
    selected: list[Symptom] = Field(default_factory=list)
    other: str | None = Field(default=None, max_length=500)
    @field_validator("selected", mode="before")
    @classmethod
    def normalize_symptom_case(cls, value):
        if not isinstance(value, list):
            return value
        return [
            item.strip().capitalize() if isinstance(item, str) else item
            for item in value
        ]


class VisitLogBase(BaseModel):
    mother_id: UUID
    visit_date: date = Field(default_factory=date.today)
    weight: float = Field(..., gt=0, le=300, description="Mother's weight in kg")
    gestational_age: int = Field(..., ge=0, le=45, description="Gestational age in weeks")
    systolic_bp: int = Field(..., ge=40, le=250)
    diastolic_bp: int = Field(..., ge=30, le=150)
    logged_symptoms: LoggedSymptoms


class VisitLogCreate(VisitLogBase):
    """What the CHV submits in the POST body."""
    pass

class VisitLogResponse(VisitLogBase):
    """What the API returns — includes server-computed fields."""
    visit_id: UUID
    pregnancy_id: UUID
    chv_id: UUID
    risk_level: str
    confidence_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class VisitTrendPoint(BaseModel):
    """Lightweight shape for the risk-trend graph."""
    visit_date: date
    risk_level: str
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)









   





