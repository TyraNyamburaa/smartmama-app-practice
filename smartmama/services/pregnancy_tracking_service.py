import uuid
from sqlalchemy.orm import Session
from smartmama.repositories import pregnancy_tracking_repository as repository
from smartmama.schemas import pregnancy_tracking_schema as schemas
from smartmama.models.mother_model import Mother


def process_new_pregnancy(db: Session, pregnancy_data: schemas.PregnancyCreate):
    mother = db.query(Mother).filter(Mother.mother_id == pregnancy_data.mother_id).first()
    if not mother:
        raise ValueError("Mother not found")

    return repository.create_pregnancy_record(db, pregnancy_data)


def fetch_pregnancy_details(db: Session, pregnancy_id: uuid.UUID):
    record = repository.get_pregnancy_by_id(db, pregnancy_id)
    if not record:
        raise ValueError("Pregnancy record not found")
    return record


def update_pregnancy(db: Session, pregnancy_id: uuid.UUID, pregnancy_data: schemas.PregnancyUpdate):
    db_pregnancy = repository.get_pregnancy_by_id(db, pregnancy_id)
    if not db_pregnancy:
        raise ValueError("Pregnancy record not found")
    return repository.update_pregnancy_record(db=db, db_pregnancy=db_pregnancy, pregnancy_data=pregnancy_data)


def get_mother_pregnancies(db: Session, mother_id: uuid.UUID):
    mother = db.query(Mother).filter(Mother.mother_id == mother_id).first()
    if not mother:
        raise ValueError("Mother not found")

    return repository.get_pregnancies_by_mother(db, mother_id)
