import hashlib
import pyotp
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID
import bcrypt
from dotenv import load_dotenv
load_dotenv()
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from smartmama.models.chv import CHV
from smartmama.repositories.chv_repository import chv_repository
from smartmama.repositories.admin_repository import admin_repository
from smartmama.models.token_model import RevokedToken

def _load_key(env_var: str, filename: str) -> str:
    key: str | None = os.getenv(env_var)
    if key:
        return key.replace("\\n", "\n")
    with open(filename, "r") as f:
        return f.read()

private_key: str = _load_key("JWT_PRIVATE_KEY", "private_key.pem")
public_key: str = _load_key("JWT_PUBLIC_KEY", "public_key.pem")

ALGORITHM = os.getenv("ALGORITHM", "RS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

RESET_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "15")
)

bearer_scheme = HTTPBearer(auto_error=False)

class TokenPayload(BaseModel):
    user_id: UUID
    role: str
    
def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False

def create_access_token(subject: str, role: str = "chv") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role":role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }

    return jwt.encode(payload, private_key, algorithm=ALGORITHM)

def create_password_reset_token(
    subject: str,
    user_type: str = "chv"
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": f"{user_type}_password_reset",
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES))
            .timestamp()
        ),
    }

    return jwt.encode(payload, private_key, algorithm=ALGORITHM)


def decode_password_reset_token(token: str, role: str) -> str:
    try:
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        if payload.get("type") != f"{role}_password_reset":
            raise JWTError
        subject = payload.get("sub")
        if not subject:
            raise JWTError
        return subject
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )
def _is_token_revoked(db: Session, token_str: str) -> bool:
    return db.query(RevokedToken).filter(RevokedToken.token == token_str).first() is not None

def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        if not payload.get("sub") or not payload.get("role"):
            raise JWTError
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> TokenPayload:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    if _is_token_revoked(db, credentials.credentials):
        raise HTTPException(status_code=401, detail="Token has been logged out")
 
    payload = _decode_access_token(credentials.credentials)
    try:
        user_id = UUID(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
 
    return TokenPayload(user_id=user_id, role=payload["role"])

def require_admin(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin account required")
    return current_user
 
def require_supervisor(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    if current_user.role != "supervisor":
        raise HTTPException(status_code=403, detail="Supervisor account required")
    return current_user
 
def require_super_admin(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TokenPayload:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin account required")
    profile = admin_repository.get_admin_profile_by_user_id(db, current_user.user_id)
    if not profile:
        raise HTTPException(status_code=403, detail="Super admin account required")
    if not bool(profile.is_superadmin):
        raise HTTPException(status_code=403, detail="Super admin account required")
    return current_user

def require_chv(
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CHV:
    if current_user.role != "chv":
        raise HTTPException(status_code=403, detail="CHV account required")
    chv = chv_repository.get_chv_profile_by_user_id(db, current_user.user_id)
    if not chv:
        raise HTTPException(status_code=404, detail="CHV profile not found")
    return chv

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def generate_mfa_secret() -> str:
    return pyotp.random_base32()

def verify_totp_code(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)

def create_mfa_challenge_token(user_id: str) -> str:
    """Short-lived, single-purpose — proves password was correct, nothing more."""
    now = datetime.now(timezone.utc)
    payload = {"sub": user_id, "type": "mfa_challenge",
               "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=5)).timestamp())}
    return jwt.encode(payload, private_key, algorithm=ALGORITHM)

def decode_mfa_challenge_token(token: str) -> str:
    try:
        payload = jwt.decode(token, public_key, algorithms=[ALGORITHM])
        if payload.get("type") != "mfa_challenge":
            raise JWTError
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired MFA challenge")

def require_admin_or_supervisor(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    if current_user.role not in ("admin", "supervisor"):
        raise HTTPException(status_code=403, detail="Admin or supervisor account required")
    return current_user