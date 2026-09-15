from uuid import UUID
from sqlalchemy.orm import Session
from smartmama.models.ticket_model import Ticket
from sqlalchemy import func
from smartmama.models.admin_model import Admin
from smartmama.models.user_model import User
from smartmama.models.person_model import Person

class TicketRepository:
    def get(self, db: Session, ticket_id: UUID) -> Ticket | None:
        return db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

    def list_all(self, db: Session) -> list[Ticket]:
        return db.query(Ticket).order_by(Ticket.created_at.desc()).all()

    def create(self, db: Session, data: dict) -> Ticket:
        t = Ticket(**data)
        db.add(t)
        db.commit()
        db.refresh(t)
        return t
    
    def top_solvers(self, db: Session, limit: int = 4):
        return (
            db.query(Person.first_name, Person.last_name, func.count(Ticket.ticket_id).label("solved_count"))
            .join(Admin, Admin.admin_id == Ticket.assigned_to)
            .join(User, User.user_id == Admin.user_id)
            .join(Person, Person.person_id == User.person_id)
            .filter(Ticket.status == "Solved")
            .group_by(Person.first_name, Person.last_name)
            .order_by(func.count(Ticket.ticket_id).desc())
            .limit(limit)
            .all()
        )

ticket_repository = TicketRepository()