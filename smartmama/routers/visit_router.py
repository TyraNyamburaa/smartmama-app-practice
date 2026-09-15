from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from ..security import require_chv
from ..schemas.visit_log_schema import VisitLogCreate, VisitLogResponse, VisitTrendPoint
from ..services.visit_log_service import (
    log_routine_visit,
    get_chv_visit_history,
    get_mother_visit_history,
    get_mother_risk_trend,
)
from ..models.visit_log_model import VisitLog

router = APIRouter(prefix="/visits", tags=["Visit Logs"])


@router.post("", response_model=VisitLogResponse, status_code=status.HTTP_201_CREATED)
def create_visit(
    visit_data: VisitLogCreate,
    db: Session = Depends(get_db),
    current_chv = Depends(require_chv),
):
    chv_id = current_chv.chv_id
    return log_routine_visit(db, visit_data, chv_id)
    


@router.get("/my-visits", response_model=list[VisitLogResponse])
def get_my_visit_history(
    db: Session = Depends(get_db),
    current_chv = Depends(require_chv),
):
    """All visits logged by the currently logged-in CHV."""
    chv_id = current_chv.chv_id
    return get_chv_visit_history(db, chv_id)


@router.get("/mother_history/{mother_id}", response_model=list[VisitLogResponse])
def get_mother_history(
    mother_id: UUID,
    db: Session = Depends(get_db),
    current_chv = Depends(require_chv),
):
    """Visit history for one mother. """
    chv_id = current_chv.chv_id
    return get_mother_visit_history(db, mother_id, chv_id)


@router.get("/mother/{mother_id}/trend", response_model=list[VisitTrendPoint])
def get_mother_trend(
    mother_id: UUID,
    db: Session = Depends(get_db),
    current_chv = Depends(require_chv),
):
    """risk data for graphing a mother's trend over time."""
    chv_id = current_chv.chv_id
    return get_mother_risk_trend(db, mother_id, chv_id)