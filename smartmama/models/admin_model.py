import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Admin(Base):
    __tablename__ = "admins"

    admin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
