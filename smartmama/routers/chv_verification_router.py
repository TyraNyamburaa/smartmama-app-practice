from fastapi import APIRouter, Body, Depends, HTTPException, Request
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

@router.post("/start-docupass")
async def start_docupass(current_chv: TokenPayload = Depends(require_chv), db: Session = Depends(get_db)):
    chv = db.query(CHV).filter(CHV.user_id == current_chv.user_id).first()
    if not chv:
        raise HTTPException(404, "CHV profile not found")

    callback_url = "https://api2-eu.idanalyzer.com/docupass"

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
