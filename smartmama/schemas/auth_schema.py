from pydantic import BaseModel, EmailStr
from typing import Optional
class UserSignup(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    password: str
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    message: str
    reset_url: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
class MFAEnrollResponse(BaseModel):
    secret: str
    provisioning_uri: str  # for QR code generation client-side

class MFAVerifyEnrollRequest(BaseModel):
    code: str

class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    mfa_required: bool = False
    challenge_token: Optional[str] = None  # present when mfa_required i.e adminsband supervisors

class MFAChallengeVerify(BaseModel):
    challenge_token: str
    code: str
    
class ResetOTPVerifyRequest(BaseModel):
    email: EmailStr
    otp_code: str

class SimpleResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
