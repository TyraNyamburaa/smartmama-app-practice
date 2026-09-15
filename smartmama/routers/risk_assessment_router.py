from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
import os
import uuid
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from smartmama.repositories import risk_assessment_repository as risk_repo
from smartmama.services import risk_assessment_service as risk_service
from smartmama.schemas import risk_assessment_schema as schemas
from smartmama.models.risk_assessment_model import RiskAssessment

router = APIRouter(prefix="/risk-assessments", tags=["Risk Assessments"])


class RiskAssessmentRequest(BaseModel):
    pregnancy_id: uuid.UUID
    visit_id: uuid.UUID
    risk_level: str
    confidence_score: float


@router.post("/", response_model=schemas.RiskAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_risk_assessment(payload: RiskAssessmentRequest, db: Session = Depends(get_db)):
    try:
        return risk_service.process_and_generate_assessment(
            db=db,
            pregnancy_id=payload.pregnancy_id,
            visit_id=payload.visit_id,
            risk_level=payload.risk_level,
            confidence_score=payload.confidence_score,
        )
    except ValueError as val_error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_error))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {exc}")


@router.get("/lookup", response_model=schemas.RiskAssessmentResponse)
def lookup_risk_assessment(
    mother_id: uuid.UUID = Query(..., description="Mother ID"),
    visit_id: uuid.UUID = Query(..., description="Visit ID"),
    pregnancy_id: uuid.UUID = Query(..., description="Pregnancy ID"),
    db: Session = Depends(get_db)
):
    try:
        return risk_service.lookup_risk_assessment(db=db, mother_id=mother_id, visit_id=visit_id, pregnancy_id=pregnancy_id)
    except ValueError as val_error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_error))


@router.get("/{risk_id}", response_model=schemas.RiskAssessmentResponse)
def read_risk_assessment(risk_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return risk_service.get_risk_assessment(db=db, risk_id=risk_id)
    except ValueError as val_error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_error))


@router.get("/pregnancy/{pregnancy_id}", response_model=list[schemas.RiskAssessmentResponse])
def read_risks_by_pregnancy(pregnancy_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return risk_service.get_risks_by_pregnancy(db=db, pregnancy_id=pregnancy_id)
    except ValueError as val_error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_error))


@router.patch("/{risk_id}", response_model=schemas.RiskAssessmentResponse)
def update_risk_assessment(risk_id: uuid.UUID, payload: schemas.RiskAssessmentUpdate, db: Session = Depends(get_db)):
    try:
        return risk_service.update_risk_assessment(db=db, risk_id=risk_id, risk_data=payload)
    except ValueError as val_error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_error))


@router.get("/download/{filename}")
def download_pdf(
    filename: str,
    db: Session = Depends(get_db),
):
    safe_filename = os.path.basename(filename)

    if not risk_repo.is_pdf_authorized(db=db, filename=filename):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PDF access has not been authorized",
        )

    try:
        file_path = risk_service.get_report_file(filename)
    except ValueError as val_error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_error))

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"risk_report_{safe_filename}",
        headers={"Content-Disposition": f"attachment; filename=risk_report_{safe_filename}"}
    )


@router.get("/mother/{mother_id}/download/{filename}")
def download_pdf_for_mother(
    mother_id: UUID,
    filename: str,
    db: Session = Depends(get_db),
):
    safe_filename = os.path.basename(filename)

    assessment = risk_repo.get_pdf_by_filename_and_mother(db=db, filename=safe_filename, mother_id=mother_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found or not authorized for this mother",
        )

    try:
        file_path = risk_service.get_report_file(safe_filename)
    except ValueError as val_error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_error))

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"risk_report_{safe_filename}",
        headers={"Content-Disposition": f"attachment; filename=risk_report_{safe_filename}"}
    )
