
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from uuid import UUID
from smartmama.schemas.auth_schema import UserSignup
from smartmama.schemas.admin_schema import AdminResponse, AdminInviteSignupRequest, AdminUpdateProfile
from smartmama.services import admin_service
from smartmama.repositories.admin_repository import admin_repository
from smartmama.security import require_super_admin, require_admin, TokenPayload

router = APIRouter(
    prefix="/admins",
    tags=["Administrator Core Profiles"]
)


@router.post(
    "/invite", 
    status_code=status.HTTP_201_CREATED
)
def invite_admin(
    data: UserSignup, 
    db: Session = Depends(get_db),
    current_super: TokenPayload = Depends(require_super_admin) #Superadmins only
):
    
    try:
        raw_token = admin_service.invite_new_admin(db, data)
        
        invite_url = f"http://localhost:3000/accept-admin-invite?token={raw_token}"
        return {
            "message": "Administrator record pre-staged successfully. Verification invitation token generated.",
            "invite_token": raw_token,
            "invite_url": invite_url
        }
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.post(
    "/register",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_admin(
    data: UserSignup,
    db: Session = Depends(get_db),
):
    try:
        profile = admin_service.register_admin(db, data)
        return {
            "admin_id": profile.admin_id,
            "user_id": profile.user_id,
            "first_name": profile.user.person.first_name,
            "last_name": profile.user.person.last_name,
            "email": profile.user.email,
            "phone_number": profile.user.person.phone_number,
            "is_superadmin": profile.is_superadmin,
            "created_at": profile.user.created_at,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.post(
    "/complete-onboarding", 
    response_model=AdminResponse, 
    status_code=status.HTTP_200_OK
)
def complete_onboarding(
    data: AdminInviteSignupRequest, 
    db: Session = Depends(get_db)
):
    
    try:
        profile = admin_service.complete_admin_onboarding(db, data)
        
        return {
            "admin_id": profile.admin_id,
            "user_id": profile.user_id,
            "first_name": profile.user.person.first_name,
            "last_name": profile.user.person.last_name,
            "email": profile.user.email,
            "phone_number": profile.user.person.phone_number,
            "is_superadmin": profile.is_superadmin,
            "created_at": profile.user.created_at
        }
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/current", 
    response_model=AdminResponse
)
def get_current_admin_profile(
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    
    profile = admin_repository.get_admin_profile_by_user_id(db, current_user.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Administrative identity record not found.")
        
    return {
        "admin_id": profile.admin_id,
        "user_id": profile.user_id,
        "first_name": profile.user.person.first_name,
        "last_name": profile.user.person.last_name,
        "email": profile.user.email,
        "phone_number": profile.user.person.phone_number,
        "is_superadmin": profile.is_superadmin,
        "created_at": profile.user.created_at
    }
@router.get("", response_model=list[AdminResponse]) 
def list_admins(
    skip: int = 0,
    limit: int = 20,
    current_super: TokenPayload = Depends(require_super_admin),  # super admin only, matches /invite
    db: Session = Depends(get_db),
):
    admins = admin_repository.list_admins(db, skip=skip, limit=limit)
    return [
        {
            "admin_id": a.admin_id,
            "user_id": a.user_id,
            "first_name": a.user.person.first_name,
            "last_name": a.user.person.last_name,
            "email": a.user.email,
            "phone_number": a.user.person.phone_number,
            "is_superadmin": a.is_superadmin,
            "created_at": a.user.created_at,
            "mfa_enabled": a.user.mfa_enabled,
        }
        for a in admins
    ]


@router.patch(
    "/profile", 
    response_model=AdminResponse
)
def modify_admin_profile(
    data: AdminUpdateProfile,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(require_admin),
):
    
    profile = admin_repository.get_admin_profile_by_user_id(db, current_user.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Administrative identity record not found.")
        
    try:
        updated_profile = admin_service.update_admin_profile(db=db, admin=profile, data=data)
        return {
            "admin_id": updated_profile.admin_id,
            "user_id": updated_profile.user_id,
            "first_name": updated_profile.user.person.first_name,
            "last_name": updated_profile.user.person.last_name,
            "email": updated_profile.user.email,
            "phone_number": updated_profile.user.person.phone_number,
            "is_superadmin": updated_profile.is_superadmin,
            "created_at": updated_profile.user.created_at
        }
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

@router.patch("/{admin_id}/deactivate", response_model=AdminResponse)
def deactivate_admin(admin_id: UUID, db: Session = Depends(get_db),
    current_super: TokenPayload = Depends(require_super_admin)):
    admin = admin_repository.get_admin_profile(db, admin_id)
    if not admin: raise HTTPException(404, "Admin not found")
    return admin_service.deactivate_admin(db, admin, current_super.user_id)