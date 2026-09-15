from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: UUID
    actor_id: Optional[UUID] = None
    email_attempted: Optional[str] = None
    event_category: str
    action_type: str
    success: Optional[bool] = None
    target_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime