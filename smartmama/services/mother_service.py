from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from smartmama.repositories.mother_repository import mother_repository
from smartmama.security import hash_password
from smartmama.repositories import audit_log_repository
from smartmama.models.mother_model import Mother

def register_mother(db: Session, data, chv_id: UUID):
    person_data = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "phone_number": data.phone_number,
        "location_name": data.location_name
    }
    mother_data = {
        "chv_id":chv_id,
        "date_of_birth": data.date_of_birth,
        "hashed_pin": hash_password(data.pin),
        "consent_given": data.consent_given,
    }
    return mother_repository.create_mother_profile(db, person_data, mother_data)


def get_mothers(db: Session, chv_id: UUID):
    return mother_repository.get_mothers_profile(db, chv_id)


def get_mother(db: Session, mother_id: UUID, chv_id: UUID):
    result = mother_repository.get_mother_profile(db, mother_id, chv_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mother not found"
        )

    return result


def update_mother(db: Session, mother_id: UUID, chv_id: UUID, data):
    db_mother = get_mother(db, mother_id, chv_id)

    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if "pin" in update_data:
        update_data["hashed_pin"] = hash_password(
            update_data.pop("pin")
        )

    return mother_repository.update_mother_profile(db, db_mother, update_data)

def reassign_mother(db: Session, mother: Mother, new_chv_id: UUID, supervisor_user_id: UUID) -> Mother:
    mother.chv_id = new_chv_id
    audit_log_repository.create(db, actor_id=supervisor_user_id, event_category="action",
                                action_type="mother_reassigned", target_id=mother.mother_id, success=True)
    db.commit(); db.refresh(mother)
    return mother







