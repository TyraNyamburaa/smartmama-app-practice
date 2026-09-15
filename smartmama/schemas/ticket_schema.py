from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TicketStatus(str, Enum):
    UNASSIGNED = "Unassigned"
    PENDING = "Pending"
    SOLVED = "Solved"
    OVERDUE = "Overdue"
    UNSOLVED = "Unsolved"

class TicketPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class TicketRespond(BaseModel):
    status: TicketStatus
    note: Optional[str] = None

class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ticket_id: UUID
    feature: str
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    raised_by_type: Optional[str] = None
    raised_by_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    response_note: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
class TicketCreate(BaseModel):
    feature: str
    title: str
    description: Optional[str] = None
    priority: TicketPriority = TicketPriority.MEDIUM