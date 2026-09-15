from uuid import UUID
from sqlalchemy.orm import Session
from smartmama.models.supervisor_model import Supervisor

class SupervisorRepository:
    def __init__(self):
        self.model = Supervisor

    def get_supervisor_profile(self, db: Session, supervisor_id: UUID) -> Supervisor | None:
        
        return (
            db.query(self.model)
            .filter(self.model.supervisor_id == supervisor_id)
            .first()
        )

    def get_supervisor_profile_by_user_id(self, db: Session, user_id: UUID) -> Supervisor | None:
        
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .first()
        )

    def create_supervisor_profile(self, db: Session, user_id: UUID) -> Supervisor:
        
        db_supervisor = self.model(
            user_id=user_id
        )
        db.add(db_supervisor)
        db.commit()
        db.refresh(db_supervisor)
        return db_supervisor

    def delete_supervisor_profile(self, db: Session, supervisor: Supervisor) -> Supervisor:
       
        if supervisor.user:
            supervisor.user.is_active = False
            db.commit()
            db.refresh(supervisor)
        return supervisor

    def list_supervisors(self, db: Session, skip: int = 0, limit: int = 20) -> list[Supervisor]:
        return (
            db.query(self.model)
            .order_by(self.model.supervisor_id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def count_supervisors(self, db: Session) -> int:
        return db.query(self.model).count()

supervisor_repository = SupervisorRepository()
