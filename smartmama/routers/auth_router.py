from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from smartmama.schemas.auth_schema import (
    UserLogin,
    LoginResponse, 
    TokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetOTPVerifyRequest,
    SimpleResetPasswordRequest,
    MFAChallengeVerify,
    MFAEnrollResponse,
    MFAVerifyEnrollRequest
)
from smartmama.services import auth_service
from smartmama.security import bearer_scheme, get_current_user, TokenPayload

router = APIRouter(
    prefix="/auth",
    tags=["Global System Authentication"]
)

@router.post("/login", response_model=LoginResponse)
def user_login(data: UserLogin, db: Session = Depends(get_db)):
    
    try:
        return auth_service.authenticate_user(db, data)
    except ValueError as error:
        raise HTTPException(
            status_code=401, detail=str(error)
        )
        
@router.post("/mfa/verify", response_model=TokenResponse)
def verify_mfa(data: MFAChallengeVerify, db: Session = Depends(get_db)):
    try:
        token = auth_service.verify_mfa_and_login(db, data.challenge_token, data.code)
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))

@router.post("/mfa/enroll", response_model=MFAEnrollResponse)
def enroll_mfa(db: Session = Depends(get_db), current_user: TokenPayload = Depends(get_current_user)):
    return auth_service.enroll_mfa(db, current_user.user_id)

@router.post("/mfa/enroll/confirm", status_code=200)
def confirm_mfa(data: MFAVerifyEnrollRequest, db: Session = Depends(get_db),
                 current_user: TokenPayload = Depends(get_current_user)):
    try:
        auth_service.confirm_mfa_enrollment(db, current_user.user_id, data.code)
        return {"message": "MFA enabled"}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.send_reset_otp(db, data.email)

@router.post("/reset-otp/verify")
def verify_reset_otp(data: ResetOTPVerifyRequest, db: Session = Depends(get_db)):
    return auth_service.verify_reset_otp(db, data.email, data.otp_code)

@router.post("/reset-password")
def reset_password(data: SimpleResetPasswordRequest, db: Session = Depends(get_db)):
    return auth_service.reset_password_after_otp(db, data.email, data.new_password)

@router.post("/logout", status_code=status.HTTP_200_OK)
def user_logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user) # Enforces token legitimacy before blacklisting
):
        
    auth_service.revoke_user_token(db, credentials.credentials)
    return {"message": "You have been logged out successfully."}

