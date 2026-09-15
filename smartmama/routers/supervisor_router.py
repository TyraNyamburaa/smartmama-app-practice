from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from smartmama.schemas.auth_schema import UserSignup
from smartmama.schemas.supervisor_schema import SupervisorResponse, SupervisorInviteSignupRequest, SupervisorUpdateProfile
from smartmama.services import supervisor_service
from smartmama.services.chv_verification_service import supervisor_verify_chv
from smartmama.repositories.supervisor_repository import supervisor_repository
from smartmama.security import require_admin, require_supervisor, TokenPayload
from smartmama.models.chv import CHV
from smartmama.models.mother_model import Mother
from smartmama.models.user_model import User

router = APIRouter(
    prefix="/supervisors",
    tags=["Supervisor Core Profiles"]
)

@router.post(
    "/invite", 
    status_code=status.HTTP_201_CREATED
)
def invite_supervisor(
    data: UserSignup, 
    db: Session = Depends(get_db),
    current_admin: TokenPayload = Depends(require_admin) 
):
   
    try:
        raw_token = supervisor_service.invite_new_supervisor(db, data)
        invite_url = f"http://localhost:3000/accept-supervisor-invite?token={raw_token}"
        return {
            "message": "Supervisor record pre-staged successfully. Onboarding token generated.",
            "invite_token": raw_token,
            "invite_url": invite_url
        }
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

@router.post(
    "/complete-onboarding", 
    response_model=SupervisorResponse, 
    status_code=status.HTTP_200_OK
)
def complete_onboarding(
    data: SupervisorInviteSignupRequest, 
    db: Session = Depends(get_db)
):
    
    try:
        profile = supervisor_service.complete_supervisor_onboarding(db, data)
        
        return {
            "supervisor_id": profile.supervisor_id,
            "user_id": profile.user_id,
            "first_name": profile.user.person.first_name,
            "last_name": profile.user.person.last_name,
            "email": profile.user.email,
            "phone_number": profile.user.person.phone_number,
            "created_at": profile.user.created_at
        }
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

@router.get(
    "/current", 
    response_model=SupervisorResponse
)
def get_current_supervisor_profile(
    current_user: TokenPayload = Depends(require_supervisor), # Open to Supervisors and Admins
    db: Session = Depends(get_db)
):
   
    profile = supervisor_repository.get_supervisor_profile_by_user_id(db, current_user.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Supervisor profile record not found.")
        
    return {
        "supervisor_id": profile.supervisor_id,
        "user_id": profile.user_id,
        "first_name": profile.user.person.first_name,
        "last_name": profile.user.person.last_name,
        "email": profile.user.email,
        "phone_number": profile.user.person.phone_number,
        "created_at": profile.user.created_at
    }

@router.patch(
    "/profile", 
    response_model=SupervisorResponse
)
def modify_supervisor_profile(
    data: SupervisorUpdateProfile,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(require_supervisor)
):
    
    profile = supervisor_repository.get_supervisor_profile_by_user_id(db, current_user.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Supervisor profile record not found.")
        
    try:
        updated_profile = supervisor_service.update_supervisor_profile(db=db, supervisor=profile, data=data)
        return {
            "supervisor_id": updated_profile.supervisor_id,
            "user_id": updated_profile.user_id,
            "first_name": updated_profile.user.person.first_name,
            "last_name": updated_profile.user.person.last_name,
            "email": updated_profile.user.email,
            "phone_number": updated_profile.user.person.phone_number,
            "created_at": updated_profile.user.created_at
        }
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    
@router.get("", response_model=list[SupervisorResponse])
def list_supervisors(
    skip: int = 0,
    limit: int = 20,
    current_admin: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db),
):
    supervisors = supervisor_repository.list_supervisors(db, skip=skip, limit=limit)
    return [
        {
            "supervisor_id": s.supervisor_id,
            "user_id": s.user_id,
            "first_name": s.user.person.first_name,
            "last_name": s.user.person.last_name,
            "email": s.user.email,
            "phone_number": s.user.person.phone_number,
            "created_at": s.user.created_at,
        }
        for s in supervisors
    ]

@router.patch("/{supervisor_id}/deactivate", response_model=SupervisorResponse)
def deactivate_supervisor(supervisor_id: UUID, db: Session = Depends(get_db),
                           current_admin: TokenPayload = Depends(require_admin)):
    supervisor = supervisor_repository.get_supervisor_profile(db, supervisor_id)
    if not supervisor: raise HTTPException(404, "Supervisor not found")
    return supervisor_service.deactivate_supervisor(db, supervisor, current_admin.user_id)

@router.get("/chvs")
def list_chvs(
    current_supervisor: TokenPayload = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """List all CHVs for supervisor oversight."""
    chvs = db.query(CHV).join(CHV.user).join(User.person).all()
    return [
        {
            "chv_id": str(c.chv_id),
            "first_name": c.user.person.first_name,
            "last_name": c.user.person.last_name,
            "email": c.user.email,
            "phone_number": c.user.person.phone_number,
            "certificate_status": c.certificate_status,
            "status": "active" if c.user.is_active else "inactive",
            "assigned_mothers": len(c.mothers),
        }
        for c in chvs
    ]

@router.get("/mothers")
def list_mothers(
    current_supervisor: TokenPayload = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    """List all mothers under supervision."""
    mothers = db.query(Mother).join(Mother.person).all()
    return [
        {
            "mother_id": str(m.mother_id),
            "first_name": m.person.first_name,
            "last_name": m.person.last_name,
            "phone_number": m.person.phone_number,
            "chv_name": f"{m.chv.user.person.first_name} {m.chv.user.person.last_name}" if m.chv and m.chv.user and m.chv.user.person else "Unassigned",
            "consent_given": m.consent_given,
            "due_date": m.date_of_birth.isoformat() if m.date_of_birth else None,
        }
        for m in mothers
    ]

@router.get("/chv-verifications")
def list_pending_chvs(current_supervisor: TokenPayload = Depends(require_supervisor), db: Session = Depends(get_db)):
    chvs = (
        db.query(CHV)
        .join(CHV.user)
        .join(User.person)
        .filter(CHV.certificate_status == "Pending")
        .all()
    )

    return [
        {
            "chv_id": str(c.chv_id),
            "first_name": c.user.person.first_name,
            "last_name": c.user.person.last_name,
            "email": c.user.email,
            "phone_number": c.user.person.phone_number,
            "certificate_number": c.certificate_number,
            "document_url": c.document_url,
            "submitted_at": c.created_at.isoformat(),
        }
        for c in chvs
    ]


@router.patch("/chv-verifications/{chv_id}")
def verify_chv(
    chv_id: UUID,
    decision: str,
    rejection_notes: str | None = None,
    current_supervisor: TokenPayload = Depends(require_supervisor),
    db: Session = Depends(get_db),
):
    sup_profile = supervisor_repository.get_supervisor_profile_by_user_id(db, current_supervisor.user_id)
    if not sup_profile:
        raise HTTPException(status_code=404, detail="Supervisor profile not found")

    try:
        updated = supervisor_verify_chv(
            db=db,
            chv_id=chv_id,
            supervisor_id=sup_profile.supervisor_id,
            decision=decision,
            rejection_notes=rejection_notes,
        )
        return {
            "chv_id": str(updated.chv_id),
            "certificate_status": updated.certificate_status,
            "verified_by": str(updated.verified_by),
            "verified_at": updated.verified_at.isoformat() if updated.verified_at else None,
            "rejection_notes": updated.rejection_notes,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))