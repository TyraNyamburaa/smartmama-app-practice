from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from smartmama.models.ticket_model import Ticket
from smartmama.repositories.ticket_repository import ticket_repository
from smartmama.repositories.audit_log_repository import audit_log_repository

def claim_ticket(db: Session, ticket: Ticket, admin_user_id: UUID, admin_id: UUID) -> Ticket:
    ticket.assigned_to = admin_id
    ticket.status = "Pending"
    audit_log_repository.create(
        db, actor_id=admin_user_id, event_category="action",
        action_type="ticket_claimed", target_id=ticket.ticket_id, success=True,
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def respond_to_ticket(db: Session, ticket: Ticket, admin_user_id: UUID, status: str, note: str | None) -> Ticket:
    ticket.status = status
    ticket.response_note = note
    if status == "Solved":
        ticket.resolved_at = datetime.now(timezone.utc)
    audit_log_repository.create(
        db, actor_id=admin_user_id, event_category="action",
        action_type="ticket_responded", target_id=ticket.ticket_id,
        success=True, details=note,
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def raise_ticket(db: Session, data: dict, raiser_user_id: UUID, raiser_role: str) -> Ticket:
    data["raised_by_id"] = raiser_user_id
    data["raised_by_type"] = raiser_role
    ticket = ticket_repository.create(db, data)
    audit_log_repository.create(
        db, actor_id=raiser_user_id, event_category="action",
        action_type="ticket_raised", target_id=ticket.ticket_id, success=True,
    )
    db.commit()
    return ticket