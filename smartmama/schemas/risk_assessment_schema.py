from pydantic import BaseModel
from datetime import date, datetime
from enum import Enum
from typing import Optional
import uuid


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            lowered = value.lower()
            for member in cls:
                if member.value == lowered:
                    return member
        return None


class RiskAssessmentBase(BaseModel):
    pregnancy_id: uuid.UUID
    mother_id: uuid.UUID
    visit_id: uuid.UUID
    risk_level: RiskLevel
    confidence_score: float
    link_url: str

    class Config:
        from_attributes = True


class RiskAssessmentCreate(RiskAssessmentBase):
    pass


class RiskAssessmentUpdate(BaseModel):
    risk_level: Optional[RiskLevel] = None
    confidence_score: Optional[float] = None
    link_url: Optional[str] = None

    class Config:
        from_attributes = True


class RiskAssessmentResponse(RiskAssessmentBase):
    risk_id: uuid.UUID
    created_at: datetime
