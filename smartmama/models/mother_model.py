import uuid
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Mother(Base):
    __tablename__ = "mothers"

    mother_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("person.person_id"), nullable=False, unique=True)
    chv_id = Column(UUID(as_uuid=True), ForeignKey("chvs.chv_id"), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("location.location_id"), nullable=True)
    hashed_pin = Column(String(255), nullable=False)
    consent_given = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    chv = relationship("CHV", back_populates="mothers")
    location = relationship(
        "Location",
        uselist=False,
        foreign_keys="[Mother.location_id]",
        primaryjoin="Mother.location_id == Location.location_id",
    )
    pregnancies = relationship("Pregnancy", back_populates="mother")
    visit_logs = relationship("VisitLog", back_populates="mother")
    risk_assessments = relationship("RiskAssessment", back_populates="mother")
    person = relationship("Person")
