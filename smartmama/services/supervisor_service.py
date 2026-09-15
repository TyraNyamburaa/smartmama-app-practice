from datetime import datetime, timedelta, timezone
from uuid import UUID
import secrets
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from smartmama.models.supervisor_model import Supervisor
from smartmama.models.user_model import User
from smartmama.repositories.supervisor_repository import supervisor_repository
from smartmama.repositories.user_repository import user_repository
from smartmama.repositories.system_token_repository import system_token_repository
from smartmama.repositories.audit_log_repository import audit_log_repository
from smartmama.schemas.auth_schema import UserSignup
from smartmama.schemas.supervisor_schema import SupervisorInviteSignupRequest, SupervisorUpdateProfile
from smartmama.security import hash_password, hash_token

INVITE_TOKEN_EXPIRE_HOURS = 48

def invite_new_supervisor(db: Session, data: UserSignup) -> str:
    
    email = str(data.email).lower()
    existing_user = user_repository.get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address is already registered."
        )

    person_data = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "phone_number": data.phone_number,
        "location_name": None
    }
    
    user_data = {
        "email": email,
        "hashed_password": hash_password(secrets.token_urlsafe(16)),  
        "role": "supervisor",
        "is_active": False 
    }
    new_user = user_repository.create_user_and_person(db, person_data, user_data)
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=INVITE_TOKEN_EXPIRE_HOURS)
    system_token_repository.create_token(
        db=db,
        token_hash=hash_token(raw_token),
        token_type="invitation",
        target_person_id=new_user.person_id,
        expires_at=expires_at
    )

    return raw_token

def complete_supervisor_onboarding(db: Session, data: SupervisorInviteSignupRequest) -> Supervisor:
    
    db_token = system_token_repository.get_valid_token(db, data.token)
    if not db_token or db_token.token_type != "invitation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The invitation link is invalid or has expired."
        )

    user = db.query(User).filter(User.person_id == db_token.target_person_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user identity data was not found."
        )

    user.hashed_password = hash_password(data.password)
    user.is_active = True

    system_token_repository.update_token_status(db, db_token, "ACCEPTED")

    new_supervisor_profile = supervisor_repository.create_supervisor_profile(
        db=db,
        user_id=user.user_id
    )

    db.commit()
    return new_supervisor_profile

def update_supervisor_profile(db: Session, supervisor: Supervisor, data: SupervisorUpdateProfile) -> Supervisor:
    
    values = data.model_dump(exclude_unset=True)

    person_updates = {}
    if "first_name" in values: person_updates["first_name"] = values.pop("first_name")
    if "last_name" in values: person_updates["last_name"] = values.pop("last_name")
    if "phone_number" in values: person_updates["phone_number"] = values.pop("phone_number")
    
    if person_updates:
        for key, val in person_updates.items():
            setattr(supervisor.user.person, key, val)

    user_updates = {}
    if "email" in values:
        email = str(values.pop("email")).lower()
        existing = user_repository.get_user_by_email(db, email)
        if existing and existing.user_id != supervisor.user_id:
            raise HTTPException(status_code=409, detail="Email already exists.")
        user_updates["email"] = email
        
    if "password" in values:
        user_updates["hashed_password"] = hash_password(values.pop("password"))

    if user_updates:
        for key, val in user_updates.items():
            setattr(supervisor.user, key, val)

    db.commit()
    db.refresh(supervisor)
    return supervisor

def deactivate_supervisor(db: Session, supervisor: Supervisor, admin_user_id: UUID) -> Supervisor:
    supervisor.user.is_active = False
    audit_log_repository.create(db, actor_id=admin_user_id, event_category="action",
                                 action_type="supervisor_deactivated", target_id=supervisor.supervisor_id, success=True)
    db.commit(); db.refresh(supervisor)
    return supervisor