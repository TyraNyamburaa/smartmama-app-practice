from uuid import UUID
from sqlalchemy.orm import Session

from ..models.visit_log_model import VisitLog
from ..models.pregnancy_tracking_model import Pregnancy
from ..schemas.visit_log_schema import VisitLogCreate


def get_active_pregnancy_id(db: Session, mother_id: UUID) -> UUID | None:
    pregnancy = (
        db.query(Pregnancy)
        .filter(
            Pregnancy.mother_id == mother_id, 
            Pregnancy.pregnancy_status.ilike("active") #  case-insensitive
        )
        .first()
    )
    return pregnancy.pregnancy_id if pregnancy else None



def create_visit_log(
    db: Session,
    visit_data: VisitLogCreate,
    pregnancy_id: UUID,
    chv_id: UUID,
    risk_level: str,
    confidence_score: float,
) -> VisitLog:
    db_visit_log = VisitLog(
        mother_id=visit_data.mother_id,
        pregnancy_id=pregnancy_id,
        chv_id=chv_id,
        visit_date=visit_data.visit_date,
        weight=visit_data.weight,
        gestational_age=visit_data.gestational_age,
        systolic_bp=visit_data.systolic_bp,
        diastolic_bp=visit_data.diastolic_bp,
        logged_symptoms=visit_data.logged_symptoms.model_dump(),
        risk_level=risk_level,
        confidence_score=confidence_score,
    )
    db.add(db_visit_log)
    db.commit()
    db.refresh(db_visit_log)
    return db_visit_log


def get_visits_by_chv(db: Session, chv_id: UUID) -> list[VisitLog]:
    return (
        db.query(VisitLog)
        .filter(VisitLog.chv_id == chv_id)
        .order_by(VisitLog.visit_date.desc())
        .all()
    )


def get_visits_by_mother(db: Session, mother_id: UUID, chv_id: UUID) -> list[VisitLog]:
    return (
        db.query(VisitLog)
        .filter(VisitLog.mother_id == mother_id, VisitLog.chv_id == chv_id)
        .order_by(VisitLog.visit_date.asc())
        .all()
    )