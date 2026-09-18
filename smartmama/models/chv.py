import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class CHV(Base):
    __tablename__ = "chvs"

    chv_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True
    )
    certificate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    certificate_status: Mapped[str] = mapped_column(
        String(20), default="Pending", nullable=False
    )
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supervisors.supervisor_id"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    mothers = relationship("Mother", back_populates="chv")
    visit_logs = relationship("VisitLog", back_populates="chv")
    verified_by_supervisor = relationship("Supervisor", back_populates="verified_chvs")
    user = relationship("User")



