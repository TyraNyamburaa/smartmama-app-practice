from uuid import UUID
import os
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials
from database import get_db
from smartmama.schemas.auth_schema import UserSignup, UserLogin
from smartmama.schemas.chv_schema import CHVResponse,CHVUpdateProfile
from smartmama.repositories.chv_repository import chv_repository
from smartmama.repositories.supervisor_repository import supervisor_repository
from smartmama.services import chv_service
from smartmama.services.attachment_scanner_service import attachment_scanner_service
from smartmama.security import require_chv, TokenPayload, require_supervisor, create_access_token
from smartmama.models.chv import CHV

router = APIRouter(
    prefix="/auth/chv",
    tags=["CHV"]
)


@router.post(
    "/signup",
    response_model=CHVResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(
    data: UserSignup,
    db: Session = Depends(get_db)
):
    try:
        profile=chv_service.signup(db=db, data=data)
        return {
            "chv_id": profile.chv_id,
            "user_id":profile.user_id,
            "first_name":profile.user.person.first_name,
            "last_name":profile.user.person.last_name,
            "email":profile.user.email,
            "phone_number": profile.user.person.phone_number,
            "certificate_status": profile.certificate_status,
            "created_at": profile.created_at
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

@router.post("/login")
def login(
    data: UserLogin,
    db: Session = Depends(get_db)
):
    try:
        chv = chv_service.login(db, data)
        token = create_access_token(str(chv.user_id), "chv")
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "chv_id": str(chv.chv_id),
                "user_id": str(chv.user_id),
                "first_name": chv.user.person.first_name,
                "last_name": chv.user.person.last_name,
                "email": chv.user.email,
                "phone_number": chv.user.person.phone_number,
                "certificate_status": chv.certificate_status,
                "created_at": chv.created_at.isoformat() if chv.created_at else None,
            },
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error)
        )
        
@router.get("/{chv_id}", response_model=CHVResponse)
def get_chv_by_id(
    chv_id: UUID,
    db: Session = Depends(get_db),
    current_supervisor: TokenPayload = Depends(require_supervisor),
):
    chv = chv_repository.get_chv_profile(db, chv_id)
    if not chv:
        raise HTTPException(404, "CHV not found")
    return {
        "chv_id": chv.chv_id,
        "user_id": chv.user_id,
        "first_name": chv.user.person.first_name,
        "last_name": chv.user.person.last_name,
        "email": chv.user.email,
        "phone_number": chv.user.person.phone_number,
        "certificate_status": chv.certificate_status,
        "created_at": chv.created_at,
    }
        
@router.patch("/{chv_id}/deactivate", response_model=CHVResponse)
def deactivate_chv(chv_id: UUID, reason: str, db: Session = Depends(get_db),
                    current_supervisor: TokenPayload = Depends(require_supervisor)):
    chv = chv_repository.get_chv_profile(db, chv_id)
    if not chv: raise HTTPException(404, "CHV not found")
    updated = chv_service.deactivate_chv_by_supervisor(db, chv, current_supervisor.user_id, reason)
    return {
        "chv_id": updated.chv_id,
        "user_id": updated.user_id,
        "first_name": updated.user.person.first_name,
        "last_name": updated.user.person.last_name,
        "email": updated.user.email,
        "phone_number": updated.user.person.phone_number,
        "certificate_status": updated.certificate_status,
        "created_at": updated.created_at
    }
@router.patch("/{chv_id}/certificate/approve", response_model=CHVResponse)
def approve_cert(chv_id: UUID, db: Session = Depends(get_db),
                  current_supervisor: TokenPayload = Depends(require_supervisor)):
    chv = chv_repository.get_chv_profile(db, chv_id)
    if not chv: raise HTTPException(404, "CHV not found")
    sup = supervisor_repository.get_supervisor_profile_by_user_id(db, current_supervisor.user_id)
    if not sup:
        raise HTTPException(404, "Supervisor profile not found")
    updated = chv_service.approve_certificate(db, chv, sup.supervisor_id, current_supervisor.user_id)
    return {
        "chv_id": updated.chv_id,
        "user_id": updated.user_id,
        "first_name": updated.user.person.first_name,
        "last_name": updated.user.person.last_name,
        "email": updated.user.email,
        "phone_number": updated.user.person.phone_number,
        "certificate_status": updated.certificate_status,
        "created_at": updated.created_at
        
    }
    
@router.get("/current", response_model=CHVResponse)
def get_chv_profile(
    current_chv: CHV = Depends(require_chv)
):
    return {
        "chv_id": current_chv.chv_id,
        "user_id": current_chv.user_id,
        "first_name": current_chv.user.person.first_name,
        "last_name": current_chv.user.person.last_name,
        "email": current_chv.user.email,
        "phone_number":current_chv.user.person.phone_number,
        "certificate_status": current_chv.certificate_status,
        "created_at": current_chv.created_at,
    }

@router.patch("/profile", response_model=CHVResponse)
def update_chv_profile(
    data: CHVUpdateProfile, 
    db: Session = Depends(get_db), 
    chv: CHV = Depends(require_chv)
):
    try:
        updated_chv = chv_service.update_profile(db=db, chv=chv, data=data)
        return {
            "chv_id": updated_chv.chv_id,
            "user_id": updated_chv.user_id,
            "first_name": updated_chv.user.person.first_name,
            "last_name": updated_chv.user.person.last_name,
            "email": updated_chv.user.email,
            "phone_number": updated_chv.user.person.phone_number,
            "certificate_status": updated_chv.certificate_status,
            "created_at": updated_chv.created_at,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

@router.post("/profile/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_chv: TokenPayload = Depends(require_chv)
):
    chv = chv_repository.get_chv_profile_by_user_id(db, current_chv.user_id)
    if not chv:
        raise HTTPException(status_code=404, detail="CHV profile not found")

    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "profile_photos")
    os.makedirs(upload_dir, exist_ok=True)

    filename = file.filename or ""
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG and PNG allowed.")

    safe_filename = f"{current_chv.user_id}{file_ext}"
    file_path = os.path.join(upload_dir, safe_filename)

    try:
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be under 5MB")

        with open(file_path, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    public_url = f"/api/v1/chv/profile/photo/{safe_filename}"

    try:
        scan_result = await attachment_scanner_service.scan_file_url(public_url)
        if not attachment_scanner_service.is_file_safe(scan_result):
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="File failed security scan. Please upload a clean image.")
    except HTTPException:
        raise
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=502, detail=f"Attachment scan failed: {e}")

    chv.user.person.profile_photo_url = public_url
    db.commit()
    db.refresh(chv)

    return {
        "message": "Profile photo uploaded successfully.",
        "profile_photo_url": public_url,
        "chv_id": str(chv.chv_id),
    }

@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_chv_profile(
    db: Session = Depends(get_db),
    current_chv: TokenPayload = Depends(require_chv)
):
    profile=chv_repository.get_chv_profile_by_user_id(db, current_chv.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="CHV profile record not found")
    chv_service.delete_profile(db, profile)
    return

@router.patch("/{chv_id}/certificate/reject", response_model=CHVResponse)
def reject_cert(chv_id: UUID, notes: str, db: Session = Depends(get_db),
                 current_supervisor: TokenPayload = Depends(require_supervisor)):
    chv = chv_repository.get_chv_profile(db, chv_id)
    if not chv: raise HTTPException(404, "CHV not found")
    sup = supervisor_repository.get_supervisor_profile_by_user_id(db, current_supervisor.user_id)
    if not sup:
        raise HTTPException(404, "Supervisor profile not found")
    updated = chv_service.reject_certificate(db, chv, sup.supervisor_id, current_supervisor.user_id, notes)
    return {
        "chv_id": updated.chv_id,
        "user_id": updated.user_id,
        "first_name": updated.user.person.first_name,
        "last_name": updated.user.person.last_name,
        "email": updated.user.email,
        "phone_number": updated.user.person.phone_number,
        "certificate_status": updated.certificate_status,
        "created_at": updated.created_at        
    }

@router.get("/profile/photo/{filename}")
def get_profile_photo(filename: str):
    safe_filename = os.path.basename(filename)
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "profile_photos")
    file_path = os.path.join(upload_dir, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Profile photo not found")

    return FileResponse(
        path=file_path,
        media_type="image/jpeg" if safe_filename.endswith(".jpg") or safe_filename.endswith(".jpeg") else "image/png",
        filename=safe_filename
    )
