from sqlalchemy.orm import Session
from smartmama.models import pregnancy_tracking_model as models
from smartmama.schemas import pregnancy_tracking_schema as schemas
import uuid


def create_pregnancy_record(db: Session, pregnancy_data: schemas.PregnancyCreate) -> models.Pregnancy:
    db_pregnancy = models.Pregnancy(
        pregnancy_id=uuid.uuid4(),
        mother_id=pregnancy_data.mother_id,
        last_menstrual_period=pregnancy_data.last_menstrual_period,
        expected_delivery_date=pregnancy_data.expected_delivery_date,
        gestational_age=pregnancy_data.gestational_age,
        pregnancy_status=pregnancy_data.pregnancy_status
    )

    db.add(db_pregnancy)
    db.commit()
    db.refresh(db_pregnancy)
    return db_pregnancy


def get_pregnancy_by_id(db: Session, pregnancy_id: uuid.UUID):
    return db.query(models.Pregnancy).filter(models.Pregnancy.pregnancy_id == pregnancy_id).first()


def get_pregnancies_by_mother(db: Session, mother_id: uuid.UUID):
    return db.query(models.Pregnancy).filter(models.Pregnancy.mother_id == mother_id).order_by(models.Pregnancy.created_at.desc()).all()


def update_pregnancy_record(db: Session, db_pregnancy: models.Pregnancy, pregnancy_data: schemas.PregnancyUpdate) -> models.Pregnancy:
    update_fields = pregnancy_data.model_dump(exclude_unset=True)
    for key, value in update_fields.items():
        setattr(db_pregnancy, key, value)
    db.commit()
    db.refresh(db_pregnancy)
    return db_pregnancy
