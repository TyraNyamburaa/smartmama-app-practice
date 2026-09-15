from sqlalchemy.orm import Session
from smartmama.models.audit_log_model import AuditLog


class AuditLogRepository:
    def create(self, db: Session, **kwargs) -> AuditLog:
        entry = AuditLog(**kwargs)
        db.add(entry)
        return entry 
     
    def list_all(self, db: Session, skip: int = 0, limit: int = 200):
        return (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

audit_log_repository = AuditLogRepository()
