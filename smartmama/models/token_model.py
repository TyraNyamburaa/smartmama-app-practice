import uuid
from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
from database import Base

class SystemToken(Base):
    __tablename__ = "system_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    token_type = Column(String, nullable=False) # "consent" (for mothers) OR "invitation" (for admin/supervisor onboarding)
    target_person_id = Column(UUID(as_uuid=True), ForeignKey("person.person_id"), nullable=False)     # Links to the target Person 
    status = Column(String, default="SENT") # SENT, VIEWED, ACCEPTED, EXPIRED
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    token = Column(String, primary_key=True, index=True)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ResetOTP(Base):
    __tablename__ = "reset_otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    otp_code = Column(String(12), nullable=False)  # alphanumeric
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
