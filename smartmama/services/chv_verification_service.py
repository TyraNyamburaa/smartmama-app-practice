from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from smartmama.models.chv import CHV

def mark_chv_pending_verification(db: Session, chv: CHV, document_url: str, certificate_number: str | None):
    chv.document_url = document_url
    chv.certificate_number = certificate_number
    chv.certificate_status = "Pending"
    chv.verified_by = None
    chv.verified_at = None
    chv.rejection_notes = None

    db.commit()
    db.refresh(chv)
    return chv


def apply_docupass_result_to_chv(db: Session, chv: CHV, parsed: dict):
    if parsed.get("is_approved") is True:
        chv.certificate_status = "Verified"
    else:
        chv.certificate_status = "Rejected"
        chv.rejection_notes = "Automated DocuPass verification failed."
        
    db.commit()
    db.refresh(chv)
    return chv



def supervisor_verify_chv(db: Session, chv_id: UUID, supervisor_id: UUID, decision: str, rejection_notes: str | None):
    chv = db.query(CHV).filter(CHV.chv_id == chv_id).first()
    if not chv:
        raise ValueError("CHV not found")

    if decision.lower() == "approve":
        chv.certificate_status = "Verified"
        chv.verified_by = supervisor_id
        chv.verified_at = datetime.utcnow()
        chv.rejection_notes = None

    elif decision.lower() == "reject":
        chv.certificate_status = "Rejected"
        chv.verified_by = supervisor_id
        chv.verified_at = datetime.utcnow()
        chv.rejection_notes = rejection_notes or "Certificate rejected."

    else:
        raise ValueError("Decision must be 'approve' or 'reject'.")

    db.commit()
    db.refresh(chv)
    return chv
