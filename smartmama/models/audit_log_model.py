import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)  # null when login failed & email matched no user
    email_attempted = Column(String(255), nullable=True)  # only set for auth events
    event_category = Column(String(20), nullable=False)   # "auth" | "action"
    success = Column(Boolean, nullable=True)               # meaningful for auth events
    ip_address = Column(String(45), nullable=True)
    action_type = Column(String(50), nullable=False) 
    target_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    actor = relationship("User", foreign_keys=[actor_id])