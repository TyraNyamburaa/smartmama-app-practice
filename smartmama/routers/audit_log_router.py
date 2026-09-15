from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from smartmama.schemas.audit_log_schema import AuditLogResponse
from smartmama.repositories.audit_log_repository import audit_log_repository
from smartmama.security import require_admin, TokenPayload

router = APIRouter(prefix="/admin/logs", tags=["System Logs"])

@router.get("/audit", response_model=list[AuditLogResponse])
def read_audit_logs(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: TokenPayload = Depends(require_admin),
):
    return audit_log_repository.list_all(db, skip=skip, limit=limit)



