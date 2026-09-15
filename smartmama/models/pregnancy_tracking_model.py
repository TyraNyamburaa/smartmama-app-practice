import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Pregnancy(Base):
    __tablename__ = "pregnancies"

    pregnancy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    mother_id = Column(UUID(as_uuid=True), ForeignKey("mothers.mother_id"), nullable=False)
    last_menstrual_period = Column(DateTime, nullable=False)
    expected_delivery_date = Column(DateTime, nullable=False)
    gestational_age = Column(Integer, nullable=False)
    pregnancy_status = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    mother = relationship("Mother", back_populates="pregnancies")
    visit_logs = relationship("VisitLog", back_populates="pregnancy")
    risk_assessments = relationship("RiskAssessment", back_populates="pregnancy")