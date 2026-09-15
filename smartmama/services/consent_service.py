import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from smartmama.security import hash_token
from smartmama.models import Mother
from smartmama.repositories import system_token_repository

def generate_consent_link(db: Session, mother: Mother) -> str:
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=72)
    system_token_repository.create_token(
        db=db, 
        token_hash=hash_token(raw_token), 
        token_type="consent",
        target_person_id=mother.mother_id, 
        expires_at=expires_at,
    )
    return f"http://localhost:3000/consent?token={raw_token}"