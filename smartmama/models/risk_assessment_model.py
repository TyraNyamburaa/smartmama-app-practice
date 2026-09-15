import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    risk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visit_logs.visit_id"), nullable=False)
    mother_id = Column(UUID(as_uuid=True), ForeignKey("mothers.mother_id"), nullable=False)
    pregnancy_id = Column(UUID(as_uuid=True), ForeignKey("pregnancies.pregnancy_id"), nullable=False)
    risk_level = Column(String(10), nullable=False)
    confidence_score = Column(Float, nullable=False)
    link_url = Column(String(255), nullable=False)
    pdf_password = Column(String(64), nullable=True)
    created_at = Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
        )
    
    mother = relationship("Mother", back_populates="risk_assessments")
    pregnancy = relationship("Pregnancy", back_populates="risk_assessments")