import pyotp
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from smartmama.models.token_model import ResetOTP
from smartmama.repositories.user_repository import user_repository, otp_repository
from smartmama.schemas.auth_schema import UserLogin, MFAChallengeVerify, MFAEnrollResponse
from smartmama.repositories.audit_log_repository import audit_log_repository
from smartmama.services.sms_service import dispatch_system_sms_sync
from smartmama.security import (
    create_access_token,
    create_password_reset_token,
    jwt,
    public_key,
    ALGORITHM,
    hash_password,
    verify_password,
    generate_mfa_secret,
    verify_totp_code,
    create_mfa_challenge_token,
    decode_mfa_challenge_token,
)

def authenticate_user(db: Session, data: UserLogin) -> str:
    email = str(data.email).lower()
    user = user_repository.get_user_by_email(db, email)

    if not user or not user.is_active or not verify_password(data.password, user.hashed_password):
        audit_log_repository.create(db, actor_id=user.user_id if user else None, email_attempted=email, event_category="auth", action_type="login_failed", success=False)
        db.commit()
        raise ValueError("Invalid email or password")
    
    if user.mfa_enabled:
        challenge = create_mfa_challenge_token(str(user.user_id))
        audit_log_repository.create(db, actor_id=user.user_id, email_attempted=email,
            event_category="auth", action_type="login_password_ok_mfa_pending", success=True)
        db.commit()
        return {"mfa_required": True, "challenge_token": challenge}

    audit_log_repository.create(db, actor_id=user.user_id, email_attempted=email,
        event_category="auth", action_type="login_success", success=True)
    db.commit()
    return {"mfa_required": False, "access_token": create_access_token(str(user.user_id), user.role)}

def verify_mfa_and_login(db: Session, challenge_token: str, code: str) -> str:
    user_id = decode_mfa_challenge_token(challenge_token)
    user = user_repository.get(db, UUID(user_id))
    if not user or not user.mfa_secret or not verify_totp_code(user.mfa_secret, code):
        audit_log_repository.create(db, actor_id=user.user_id if user else None,
            event_category="auth", action_type="mfa_failed", success=False)
        db.commit()
        raise ValueError("Invalid MFA code")
    audit_log_repository.create(db, actor_id=user.user_id, event_category="auth",
        action_type="login_success", success=True)
    db.commit()
    return create_access_token(str(user.user_id), user.role)

def enroll_mfa(db: Session, user_id: UUID) -> dict:
    user = user_repository.get(db, user_id)
    secret = generate_mfa_secret()
    user.mfa_secret = secret  
    db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="SmartMama")
    return {"secret": secret, "provisioning_uri": uri}

def confirm_mfa_enrollment(db: Session, user_id: UUID, code: str) -> None:
    user = user_repository.get(db, user_id)
    if not user.mfa_secret or not verify_totp_code(user.mfa_secret, code):
        raise ValueError("Invalid code — enrollment not confirmed")
    user.mfa_enabled = True
    db.commit()
    
def send_reset_otp(db: Session, email: str):
    email = email.lower()
    user = user_repository.get_user_by_email(db, email)

    if not user:
        return {"message": "An OTP has been sent."}

    phone = user.person.phone_number
    if not phone:
        raise ValueError("No phone number associated with this account.")

    import secrets
    otp_code = secrets.token_hex(3).upper()  # 6-char alphanumeric

    expires_at = datetime.utcnow() + timedelta(minutes=5)

    otp_repository.create_otp(db, user.user_id, otp_code, expires_at)

    sms_text = f"Your SmartMama password reset code is: {otp_code}. It expires in 5 minutes."

    dispatch_system_sms_sync(phone, sms_text)

    return {"message": "If this email exists, an OTP has been sent."}

def verify_reset_otp(db: Session, email: str, otp_code: str):
    email = email.lower()
    user = user_repository.get_user_by_email(db, email)

    if not user:
        raise ValueError("Invalid OTP or email.")

    otp = otp_repository.get_valid_otp(db, user.user_id, otp_code)
    if not otp:
        raise ValueError("Invalid or expired OTP.")

    otp_repository.mark_used(db, otp)

    return {"message": "OTP verified."}

def reset_password_after_otp(db: Session, email: str, new_password: str):
    email = email.lower()
    user = user_repository.get_user_by_email(db, email)

    if not user:
        raise ValueError("Invalid email.")

    used_otp = (
        db.query(ResetOTP)
        .filter(
            ResetOTP.user_id == user.user_id,
            ResetOTP.is_used == True
        )
        .order_by(ResetOTP.created_at.desc())
        .first()
    )

    if not used_otp:
        raise ValueError("OTP verification required.")

    user.hashed_password = hash_password(new_password)
    db.commit()

    return {"message": "Password reset successful."}

def revoke_user_token(db: Session, token_str: str) -> None:
    user_repository.revoke_token(db, token_str)
