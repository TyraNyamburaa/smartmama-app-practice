from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from smartmama.models.chv import CHV
from smartmama.repositories.chv_repository import chv_repository
from smartmama.repositories.user_repository import user_repository
from smartmama.repositories.audit_log_repository import audit_log_repository
from smartmama.schemas.chv_schema import CHVUpdateProfile
from smartmama.schemas.auth_schema import UserSignup, UserLogin
from smartmama.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)

def signup(db: Session, data: UserSignup) -> CHV:
    email = str(data.email).lower()
    
    existing_user = user_repository.get_user_by_email(db, email)
    if existing_user:
        raise ValueError("Email already registered")
    
    person_data = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "phone_number": data.phone_number,
    }
    
    user_data = {
        "email": email,
        "hashed_password": hash_password(data.password),
        "role": "chv",
        "is_active": True
    }
    
    new_user = user_repository.create_user_and_person(db, person_data, user_data)
    return chv_repository.create_chv_profile(db, new_user.user_id)

def login(db: Session, data: UserLogin) -> CHV:
    user = user_repository.get_user_by_email(db, str(data.email).lower())
    if not user:
        raise ValueError("Invalid credentials")
    if not verify_password(data.password, user.hashed_password):
        raise ValueError("Invalid credentials")
    if not user.is_active:
        raise ValueError("Account is deactivated")

    chv = db.query(CHV).filter(CHV.user_id == user.user_id).first()
    if not chv:
        raise ValueError("CHV profile not found")

    return chv


def update_profile(db: Session, chv: CHV, data: CHVUpdateProfile) -> CHV:
    values = data.model_dump(exclude_unset=True)
    
    person_updates = {}
    if "first_name" in values: person_updates["first_name"] = values.pop("first_name")
    if "last_name" in values: person_updates["last_name"]=values.pop("last_name")
    if "phone_number" in values: person_updates["phone_number"] = values.pop("phone_number")
    if "profile_photo_url" in values: person_updates["profile_photo_url"] = values.pop("profile_photo_url")
    if person_updates:
        for key, val in person_updates.items():
            setattr(chv.user.person, key, val)
    
    user_updates = {}    
    if "email" in values:
        email = str(values["email"]).lower()
        existing = user_repository.get_user_by_email(db, email)
        if existing and existing.user_id != chv.user_id:
            raise ValueError("Email already exists")
        user_updates["email"] = email
        
    if "password" in values:
        user_updates["hashed_password"] = hash_password(values.pop("password"))
    
    if user_updates:
        for key, val in user_updates.items():
            setattr(chv.user, key, val)
    if values:
        chv_repository.update_chv_profile(db, chv, values)
    db.commit()
    db.refresh(chv)
    return chv



def deactivate_chv_self(db: Session, chv: CHV) -> CHV:
    chv.user.is_active = False
    audit_log_repository.create(db, actor_id=chv.user_id, event_category="action",
                                action_type="chv_self_deactivated", target_id=chv.chv_id, success=True)
    db.commit(); db.refresh(chv)
    return chv

def deactivate_chv_by_supervisor(db: Session, chv: CHV, supervisor_user_id: UUID, reason: str) -> CHV:
    chv.user.is_active = False
    audit_log_repository.create(db, actor_id=supervisor_user_id, event_category="action",                                action_type="chv_deactivated_by_supervisor", target_id=chv.chv_id,
                                success=True, details=reason)
    db.commit(); db.refresh(chv)
    return chv

def approve_certificate(db: Session, chv: CHV, supervisor_id: UUID, supervisor_user_id: UUID) -> CHV:
    chv.certificate_status = "Verified"
    chv.verified_by = supervisor_id
    chv.verified_at = datetime.now(timezone.utc)
    audit_log_repository.create(db, actor_id=supervisor_user_id, event_category="action",
                                 action_type="certificate_approved", target_id=chv.chv_id, success=True)
    db.commit(); db.refresh(chv)
    return chv

def reject_certificate(db: Session, chv: CHV, supervisor_id: UUID, supervisor_user_id: UUID, notes: str) -> CHV:
    chv.certificate_status = "Rejected"
    chv.verified_by = supervisor_id
    chv.verified_at = datetime.now(timezone.utc)
    chv.rejection_notes = notes
    audit_log_repository.create(db, actor_id=supervisor_user_id, event_category="action",
                                 action_type="certificate_rejected", target_id=chv.chv_id, success=True, details=notes)
    db.commit(); db.refresh(chv)
    return chv


def delete_profile(db: Session, chv: CHV) -> None:
    user_id = chv.user_id
    chv_repository.delete_chv_profile(db, chv)
    # Soft delete user - deactivate instead of hard delete
    user = user_repository.get(db, user_id)
    if user:
        user.is_active = False
        db.commit()
