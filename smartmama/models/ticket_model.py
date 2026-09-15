import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    feature = Column(String(50), nullable=False)  
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Unassigned")  # Unassigned | Pending | Solved | Overdue | Unsolved
    priority = Column(String(10), nullable=False, default="Medium")  # High | Medium | Low
    raised_by_type = Column(String(20), nullable=True)  # "chv" | "supervisor" | null if system-generated
    raised_by_id = Column(UUID(as_uuid=True), nullable=True)  # FK target varies by raised_by_type, so no fixed ForeignKey()
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("admins.admin_id"), nullable=True)
    response_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    assignee = relationship("Admin", foreign_keys=[assigned_to])