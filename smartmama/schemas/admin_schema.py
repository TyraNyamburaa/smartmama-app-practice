from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

class AdminInviteSignupRequest(BaseModel):
    
    token: str
    password: str

class AdminResponse(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)

    admin_id: UUID
    user_id: UUID
    first_name: str            
    last_name: str             
    email: EmailStr            
    phone_number: Optional[str] = None 
    is_superadmin: bool   
    mfa_enabled: bool = False     
    created_at: datetime

class AdminUpdateProfile(BaseModel):
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
