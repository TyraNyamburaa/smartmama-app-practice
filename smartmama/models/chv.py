import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    Text,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class CHV(Base):
    __tablename__ = "chvs"

    chv_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    certificate_number = Column(String(50), nullable=True)
    document_url=Column(String(500), nullable=True)
    certificate_status = Column(String(20), default="Pending", nullable=False) # Pending/verified/rejected
    verified_by = Column(UUID(as_uuid=True), ForeignKey("supervisors.supervisor_id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    rejection_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    mothers = relationship("Mother", back_populates="chv")
    visit_logs = relationship("VisitLog", back_populates="chv")
    verified_by_supervisor = relationship("Supervisor", back_populates="verified_chvs")
    user = relationship("User")



