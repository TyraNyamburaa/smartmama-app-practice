import uuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Supervisor(Base):
    __tablename__ = "supervisors"

    supervisor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, unique=True)
    
    verified_chvs = relationship("CHV", back_populates="verified_by_supervisor")
    user = relationship("User")