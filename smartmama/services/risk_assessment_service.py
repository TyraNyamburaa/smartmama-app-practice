import os
import uuid
import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from smartmama.repositories import risk_assessment_repository as risk_repo
from smartmama.models import risk_assessment_model as models
from smartmama.schemas import risk_assessment_schema as schemas
from smartmama.models import visit_log_model as visit_models
from smartmama.services import sms_service


STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "assessments")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def _ensure_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)


def _generate_raw_pdf(mother_name, phone_number, symptoms, risk_level, confidence_score):
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=letter)
    pdf_canvas.setFont("Helvetica-Bold", 16)
    pdf_canvas.drawString(50, 750, "MATERNAL RISK REPORT")
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(50, 700, f"Mother Name: {mother_name}")
    pdf_canvas.drawString(50, 680, f"Phone Number: {phone_number}")
    pdf_canvas.drawString(50, 660, f"Symptoms: {symptoms}")
    pdf_canvas.drawString(50, 640, f"Risk Evaluation: {risk_level.upper()}")
    pdf_canvas.drawString(50, 620, f"Confidence Score: {confidence_score:.2%}")
    
    pdf_canvas.save()
    buffer.seek(0)
    return buffer.read()


def process_and_generate_assessment(db: Session, pregnancy_id: uuid.UUID, visit_id: uuid.UUID, risk_level: str | None = None, confidence_score: float | None = None):
    stored_filename = f"{uuid.uuid4()}.pdf"
    stored_path = os.path.join(STORAGE_DIR, stored_filename)

    _ensure_storage()

    visit_record = db.query(visit_models.VisitLog).filter(visit_models.VisitLog.visit_id == visit_id).first()
    if not visit_record:
        raise ValueError("Visit record not found")

    resolved_risk_level = risk_level if risk_level is not None else visit_record.risk_level
    resolved_confidence_score = confidence_score if confidence_score is not None else visit_record.confidence_score

    normalized_risk_level = resolved_risk_level.lower() if isinstance(resolved_risk_level, str) else resolved_risk_level

    mother_record = risk_repo.get_mother_record_for_assessment(
        db=db, visit_id=visit_id, pregnancy_id=pregnancy_id
    )

    if not mother_record:
        raise ValueError("Data records could not be fetched for validation.")

    full_name = f"{mother_record.first_name} {mother_record.last_name}"
    raw_pdf_bytes = _generate_raw_pdf(
        mother_name=full_name,
        phone_number=mother_record.phone_number,
        symptoms=mother_record.symptoms,
        risk_level=normalized_risk_level,
        confidence_score=resolved_confidence_score,
    )

    with open(stored_path, "wb") as f:
        f.write(raw_pdf_bytes)

    download_url = f"{BASE_URL}/api/v1/portal/month/{datetime.datetime.now().year}/{datetime.datetime.now().month}"

    assessment_data = schemas.RiskAssessmentCreate(
        pregnancy_id=pregnancy_id,
        visit_id=visit_id,
        mother_id=mother_record.mother_id,
        risk_level=normalized_risk_level,
        confidence_score=resolved_confidence_score,
        link_url=download_url
    )

    saved_assessment = risk_repo.create_risk_record(db=db, risk_data=assessment_data, confidence_score=resolved_confidence_score)

    contact = risk_repo.get_risk_with_mother_contact(db, saved_assessment.risk_id)
    if contact and contact.phone_number:
        sms_text = sms_service.build_risk_assessment_sms(
            mother_name=f"{contact.first_name} {contact.last_name}",
            portal_url=download_url,
        )
        sms_service.dispatch_system_sms_sync(contact.phone_number, sms_text)

    return saved_assessment


def lookup_risk_assessment(db: Session, mother_id: uuid.UUID, visit_id: uuid.UUID, pregnancy_id: uuid.UUID):
    verification = risk_repo.verify_mother_visit_pregnancy(
        db=db, mother_id=mother_id, visit_id=visit_id, pregnancy_id=pregnancy_id
    )

    if not verification:
        raise ValueError("No matching mother, visit, and pregnancy found")

    record = db.query(models.RiskAssessment).filter(
        models.RiskAssessment.pregnancy_id == pregnancy_id,
        models.RiskAssessment.mother_id == mother_id
    ).first()

    if not record:
        raise ValueError("Risk assessment not found for this mother and pregnancy")

    return record


def get_risk_assessment(db: Session, risk_id: uuid.UUID):
    record = risk_repo.get_risk_by_id(db=db, risk_id=risk_id)
    if not record:
        raise ValueError("Risk assessment not found")
    return record


def get_risks_by_pregnancy(db: Session, pregnancy_id: uuid.UUID):
    records = risk_repo.get_risk_by_pregnancy(db=db, pregnancy_id=pregnancy_id)
    if not records:
        raise ValueError("No risk assessments found for this pregnancy")
    return records


def _regenerate_report(db: Session, db_risk):
    visit_record = db.query(visit_models.VisitLog).filter(visit_models.VisitLog.visit_id == db_risk.visit_id).first()
    if not visit_record:
        return

    risk_level = visit_record.risk_level
    confidence_score = visit_record.confidence_score

    mother_record = risk_repo.get_mother_record_for_assessment(
        db=db, visit_id=db_risk.visit_id, pregnancy_id=db_risk.pregnancy_id
    )
    if not mother_record:
        return

    full_name = f"{mother_record.first_name} {mother_record.last_name}"
    new_filename = f"{uuid.uuid4()}.pdf"
    new_path = os.path.join(STORAGE_DIR, new_filename)

    raw_pdf_bytes = _generate_raw_pdf(
        mother_name=full_name,
        phone_number=mother_record.phone_number,
        symptoms=mother_record.symptoms,
        risk_level=risk_level,
        confidence_score=confidence_score,
    )
    with open(new_path, "wb") as f:
        f.write(raw_pdf_bytes)

    if db_risk.link_url and "/" in db_risk.link_url:
        old_filename = db_risk.link_url.rsplit("/", 1)[-1]
        if old_filename != new_filename:
            old_path = os.path.join(STORAGE_DIR, old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)

    db_risk.link_url = f"{BASE_URL}/api/v1/portal/month/{datetime.datetime.now().year}/{datetime.datetime.now().month}"
    db_risk.pdf_password = None
    db.commit()
    db.refresh(db_risk)


def update_risk_assessment(db: Session, risk_id: uuid.UUID, risk_data: schemas.RiskAssessmentUpdate):
    db_risk = risk_repo.get_risk_by_id(db=db, risk_id=risk_id)
    if not db_risk:
        raise ValueError("Risk assessment not found")
    updated = risk_repo.update_risk_record(db=db, db_risk=db_risk, risk_data=risk_data)
    changed = risk_data.model_dump(exclude_unset=True)
    if "risk_level" in changed:
        _regenerate_report(db, updated)
    return updated


def get_report_file(filename: str):
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(STORAGE_DIR, safe_filename)
    if not os.path.exists(file_path):
        raise ValueError("PDF not found")
    return file_path
