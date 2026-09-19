import os
import base64
from fastapi import APIRouter, Body, Depends, HTTPException, Request, File, UploadFile
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from smartmama.models.chv import CHV
from smartmama.security import require_chv, TokenPayload
from smartmama.services.id_analyzer_service import id_analyzer_service
from smartmama.services.attachment_scanner_service import attachment_scanner_service
from smartmama.services.chv_verification_service import (
    mark_chv_pending_verification,
    apply_docupass_result_to_chv,
)

router = APIRouter(
    prefix="/chv-verification",
    tags=["CHV Verification"]
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "chv_documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def validate_file(file: UploadFile) -> str:
    filename = file.filename or ""
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, JPG, and PNG allowed.")
    return file_ext


async def save_file(file: UploadFile, user_id: UUID, prefix: str) -> str:
    file_ext = validate_file(file)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size must be under 5MB")

    safe_filename = f"{prefix}_{user_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    return f"/api/v1/chv-verification/document/{safe_filename}"


@router.post("/verify-identity")
async def verify_identity(
    id_file: UploadFile = File(...),
    face_file: UploadFile = File(...),
    current_chv: TokenPayload = Depends(require_chv),
    db: Session = Depends(get_db)
):
    chv = db.query(CHV).filter(CHV.user_id == current_chv.user_id).first()
    if not chv:
        raise HTTPException(404, "CHV profile not found")

    validate_file(id_file)
    validate_file(face_file)

    id_content = await id_file.read()
    face_content = await face_file.read()

    id_base64 = base64.b64encode(id_content).decode("utf-8")
    face_base64 = base64.b64encode(face_content).decode("utf-8")

    try:
        raw_result = await id_analyzer_service.verify_user_identity(
            chv_id=str(chv.chv_id),
            document_base64=id_base64,
            face_base64=face_base64
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Identity verification pipeline failed: {e}")

    parsed_result = id_analyzer_service.parse_verification_result(raw_result)
    apply_docupass_result_to_chv(db, chv, parsed_result)

    return {
        "status": "Processed",
        "document_authenticity": parsed_result["document_authenticity"],
        "face_match_score": parsed_result["face_match_score"],
        "liveness_score": parsed_result["liveness_score"]
    }


@router.post("/start-docupass")
async def start_docupass(current_chv: TokenPayload = Depends(require_chv), db: Session = Depends(get_db)):
    chv = db.query(CHV).filter(CHV.user_id == current_chv.user_id).first()
    if not chv:
        raise HTTPException(404, "CHV profile not found")

    # Callback URL should point to THIS backend's docupass-callback endpoint
    callback_url = "https://smartmama-app-practice.onrender.com"

    session = await id_analyzer_service.create_docupass_session(str(chv.chv_id), callback_url)

    return {
        "docupass_url": session.get("url"),
        "reference": session.get("reference"),
    }


@router.post("/docupass-callback")
async def docupass_callback(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    reference = payload.get("reference")

    if not reference:
        raise HTTPException(400, "Missing reference")

    chv = db.query(CHV).filter(CHV.chv_id == UUID(reference)).first()
    if not chv:
        raise HTTPException(404, "CHV not found")

    parsed = id_analyzer_service.parse_docupass_result(payload)
    apply_docupass_result_to_chv(db, chv, parsed)

    return {"message": "DocuPass verification stored", "chv_id": str(chv.chv_id)}


@router.post("/submit-certificate")
async def submit_certificate(
    document_url: str = Body(..., embed=True),
    certificate_number: str | None = Body(None, embed=True),
    current_chv: TokenPayload = Depends(require_chv),
    db: Session = Depends(get_db),
):
    chv = db.query(CHV).filter(CHV.user_id == current_chv.user_id).first()
    if not chv:
        raise HTTPException(status_code=404, detail="CHV profile not found.")

    try:
        scan_result = await attachment_scanner_service.scan_file_url(document_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Attachment scan failed: {e}")

    is_safe = attachment_scanner_service.is_file_safe(scan_result)
    if not is_safe:
        chv.certificate_status = "Rejected"
        chv.rejection_notes = "Certificate file failed security scan."
        db.commit()
        db.refresh(chv)
        raise HTTPException(
            status_code=400,
            detail="Certificate file is unsafe or malicious. Upload a clean document.",
        )

    updated = mark_chv_pending_verification(
        db=db,
        chv=chv,
        document_url=document_url,
        certificate_number=certificate_number,
    )

    return {
        "message": "Certificate submitted and passed security scan.",
        "certificate_status": updated.certificate_status,
        "chv_id": str(updated.chv_id),
    }


@router.post("/upload-certificate")
async def upload_certificate(
    file: UploadFile = File(...),
    current_chv: TokenPayload = Depends(require_chv),
    db: Session = Depends(get_db),
):
    chv = db.query(CHV).filter(CHV.user_id == current_chv.user_id).first()
    if not chv:
        raise HTTPException(status_code=404, detail="CHV profile not found.")

    document_url = await save_file(file, current_chv.user_id, "certificate")

    try:
        scan_result = await attachment_scanner_service.scan_file_url(document_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Attachment scan failed: {e}")

    is_safe = attachment_scanner_service.is_file_safe(scan_result)
    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail="Certificate file is unsafe or malicious. Upload a clean document.",
        )

    return {
        "message": "Certificate uploaded and passed security scan.",
        "document_url": document_url,
    }


@router.post("/upload-id-proof")
async def upload_id_proof(
    file: UploadFile = File(...),
    current_chv: TokenPayload = Depends(require_chv),
    db: Session = Depends(get_db),
):
    chv = db.query(CHV).filter(CHV.user_id == current_chv.user_id).first()
    if not chv:
        raise HTTPException(status_code=404, detail="CHV profile not found.")

    document_url = await save_file(file, current_chv.user_id, "id_proof")

    try:
        scan_result = await attachment_scanner_service.scan_file_url(document_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Attachment scan failed: {e}")

    is_safe = attachment_scanner_service.is_file_safe(scan_result)
    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail="ID proof file is unsafe or malicious. Upload a clean document.",
        )

    return {
        "message": "ID proof uploaded and passed security scan.",
        "document_url": document_url,
    }


@router.get("/verification-status")
async def get_verification_status(
    current_chv: TokenPayload = Depends(require_chv),
    db: Session = Depends(get_db),
):
    chv = db.query(CHV).filter(CHV.user_id == current_chv.user_id).first()
    if not chv:
        raise HTTPException(status_code=404, detail="CHV profile not found.")

    return {
        "certificate_status": chv.certificate_status,
        "certificate_number": chv.certificate_number,
        "document_url": chv.document_url,
        "verified_at": chv.verified_at,
        "rejection_notes": chv.rejection_notes,
    }


@router.get("/document/{filename}")
async def get_document(filename: str):
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        media_type="application/pdf" if safe_filename.endswith(".pdf") else "image/jpeg",
        filename=safe_filename,
    )
