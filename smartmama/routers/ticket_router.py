# ticket_router.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from smartmama.schemas.ticket_schema import TicketResponse, TicketRespond, TicketCreate
from smartmama.repositories.ticket_repository import ticket_repository
from smartmama.repositories.admin_repository import admin_repository
from smartmama.services import ticket_service
from smartmama.security import require_admin, get_current_user, TokenPayload

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("", response_model=list[TicketResponse])
def list_tickets(db: Session = Depends(get_db), _: TokenPayload = Depends(require_admin)):
    return ticket_repository.list_all(db)

@router.post("/{ticket_id}/claim", response_model=TicketResponse)
def claim(ticket_id: UUID, db: Session = Depends(get_db), current_admin: TokenPayload = Depends(require_admin)):
    ticket = ticket_repository.get(db, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    admin_profile = admin_repository.get_admin_profile_by_user_id(db, current_admin.user_id)
    if not admin_profile:
        raise HTTPException(status_code=404, detail="Admin profile not found")
    return ticket_service.claim_ticket(db, ticket, current_admin.user_id, admin_profile.admin_id)

@router.patch("/{ticket_id}/respond", response_model=TicketResponse)
def respond(ticket_id: UUID, data: TicketRespond, db: Session = Depends(get_db),
            current_admin: TokenPayload = Depends(require_admin)):
    ticket = ticket_repository.get(db, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket_service.respond_to_ticket(db, ticket, current_admin.user_id, data.status.value, data.note)

@router.post("", response_model=TicketResponse, status_code=201)
def raise_ticket(data: TicketCreate, db: Session = Depends(get_db), current_user: TokenPayload = Depends(get_current_user)):
    return ticket_service.raise_ticket(db, data.model_dump(), current_user.user_id, current_user.role)

@router.get("/top-solvers")
def get_top_solvers(db: Session = Depends(get_db), _: TokenPayload = Depends(require_admin)):
    results = ticket_repository.top_solvers(db)
    return [{"name": f"{r.first_name} {r.last_name}", "tickets": r.solved_count} for r in results]