import uuid
from datetime import date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, Text, Float, Integer, Date, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import (
    Column,
    Date,
    Float,
    Integer,
    Text,
    TIMESTAMP,
    ForeignKey,
    func,
)

class VisitLog(Base):
    __tablename__ = "visit_logs"

    visit_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    mother_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mothers.mother_id"),
        nullable=False,
        index=True,
    )
    pregnancy_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("pregnancies.pregnancy_id"),  
        nullable=False, 
        index=True,
    )
    chv_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("chvs.chv_id"), 
        nullable=False, 
        index=True
    )
    visit_date = Column(Date, nullable=False, default=date.today)
    weight = Column(Float, nullable=False)
    gestational_age = Column(Integer, nullable=False)
    systolic_bp = Column(Integer, nullable=False)
    diastolic_bp = Column(Integer, nullable=False)
    blood_sugar = Column(Float, nullable=False)
    logged_symptoms = Column(JSONB, nullable=False)
    risk_level = Column(Text, nullable=False)  # "Low" | "Medium" | "High" 
    confidence_score = Column(Float, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    
    mother = relationship("Mother", back_populates="visit_logs")
    pregnancy = relationship("Pregnancy", back_populates="visit_logs")
    chv = relationship("CHV", back_populates="visit_logs")    
