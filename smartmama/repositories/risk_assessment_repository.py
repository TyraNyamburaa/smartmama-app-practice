import os
import uuid
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from smartmama.models import risk_assessment_model as models
from smartmama.models import mother_model as mother_models
from smartmama.models import visit_log_model as visit_models
from smartmama.models import pregnancy_tracking_model as pregnancy_models
from smartmama.schemas import risk_assessment_schema as schemas


def create_risk_record(db: Session, risk_data: schemas.RiskAssessmentCreate, confidence_score: float) -> models.RiskAssessment:
    new_assessment = models.RiskAssessment(
        risk_id=uuid.uuid4(),
        pregnancy_id=risk_data.pregnancy_id,
        visit_id=risk_data.visit_id,
        mother_id=risk_data.mother_id,
        risk_level=risk_data.risk_level.value,
        confidence_score=confidence_score,
        link_url=str(risk_data.link_url)
    )

    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    return new_assessment


def get_risk_by_pregnancy(db: Session, pregnancy_id: uuid.UUID):
    return db.query(models.RiskAssessment).filter(models.RiskAssessment.pregnancy_id == pregnancy_id).all()


def get_risk_by_id(db: Session, risk_id: uuid.UUID):
    return db.query(models.RiskAssessment).filter(models.RiskAssessment.risk_id == risk_id).first()


def update_risk_record(db: Session, db_risk: models.RiskAssessment, risk_data: schemas.RiskAssessmentUpdate) -> models.RiskAssessment:
    update_fields = risk_data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        setattr(db_risk, key, value)
    db.commit()
    db.refresh(db_risk)
    return db_risk


def get_mother_record_for_assessment(db: Session, visit_id: uuid.UUID, pregnancy_id: uuid.UUID):
    return db.query(
        mother_models.Mother.mother_id,
        mother_models.Mother.first_name,
        mother_models.Mother.last_name,
        mother_models.Mother.phone_number,
        visit_models.VisitLog.logged_symptoms.label("symptoms")
    ).join(
        visit_models.VisitLog, mother_models.Mother.mother_id == visit_models.VisitLog.mother_id
    ).join(
        pregnancy_models.Pregnancy, mother_models.Mother.mother_id == pregnancy_models.Pregnancy.mother_id
    ).filter(
        visit_models.VisitLog.visit_id == visit_id,
        pregnancy_models.Pregnancy.pregnancy_id == pregnancy_id
    ).first()


def verify_mother_visit_pregnancy(db: Session, mother_id: uuid.UUID, visit_id: uuid.UUID, pregnancy_id: uuid.UUID):
    return db.query(
        mother_models.Mother.mother_id,
        pregnancy_models.Pregnancy.pregnancy_id,
        visit_models.VisitLog.visit_id
    ).join(
        visit_models.VisitLog, mother_models.Mother.mother_id == visit_models.VisitLog.mother_id
    ).join(
        pregnancy_models.Pregnancy, mother_models.Mother.mother_id == pregnancy_models.Pregnancy.mother_id
    ).filter(
        mother_models.Mother.mother_id == mother_id,
        visit_models.VisitLog.visit_id == visit_id,
        pregnancy_models.Pregnancy.pregnancy_id == pregnancy_id
    ).first()


def is_pdf_authorized(db: Session, filename: str) -> bool:
    safe_filename = os.path.basename(filename)
    result = db.query(models.RiskAssessment).filter(
        models.RiskAssessment.link_url.like(f"%{safe_filename}%"),
        models.RiskAssessment.pdf_password.isnot(None)
    ).limit(1).first()
    return result is not None


def get_risk_with_mother_contact(db: Session, risk_id: uuid.UUID):
    return db.query(
        models.RiskAssessment.risk_id,
        models.RiskAssessment.link_url,
        mother_models.Mother.phone_number,
        mother_models.Mother.first_name,
        mother_models.Mother.last_name,
    ).join(
        mother_models.Mother, models.RiskAssessment.mother_id == mother_models.Mother.mother_id
    ).filter(
        models.RiskAssessment.risk_id == risk_id
    ).first()


def get_pdfs_by_mother(db: Session, mother_id: uuid.UUID):
    return db.query(
        models.RiskAssessment.risk_id,
        models.RiskAssessment.link_url,
        models.RiskAssessment.created_at,
        models.RiskAssessment.risk_level,
        extract('year', models.RiskAssessment.created_at).label('year'),
        extract('month', models.RiskAssessment.created_at).label('month'),
    ).filter(
        models.RiskAssessment.mother_id == mother_id
    ).order_by(
        models.RiskAssessment.created_at.desc()
    ).all()


def get_pdf_by_filename_and_mother(db: Session, filename: str, mother_id: uuid.UUID):
    safe_filename = os.path.basename(filename)
    return db.query(models.RiskAssessment).filter(
        models.RiskAssessment.link_url.like(f"%{safe_filename}%"),
        models.RiskAssessment.mother_id == mother_id
    ).first()
