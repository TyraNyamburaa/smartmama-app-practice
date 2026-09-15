from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from smartmama.schemas import pregnancy_tracking_schema as schemas
from smartmama.services import pregnancy_tracking_service as service

from database import get_db

router = APIRouter(
    prefix="/pregnancies",
    tags=["Pregnancy Management"]
)

@router.post("/", response_model=schemas.PregnancyResponse, status_code=201)
def create_pregnancy(payload: schemas.PregnancyCreate, db: Session = Depends(get_db)):
    try:
        return service.process_new_pregnancy(db, payload)
    except ValueError as val_error:
        raise HTTPException(status_code=404, detail=str(val_error))

@router.get("/mother/{mother_id}", response_model=list[schemas.PregnancyResponse])
def get_mother_pregnancies(mother_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return service.get_mother_pregnancies(db, mother_id)
    except ValueError as val_error:
        raise HTTPException(status_code=404, detail=str(val_error))

@router.get("/{pregnancy_id}", response_model=schemas.PregnancyResponse)
def read_pregnancy(pregnancy_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return service.fetch_pregnancy_details(db, pregnancy_id)
    except ValueError as val_error:
        raise HTTPException(status_code=404, detail=str(val_error))

@router.patch("/{pregnancy_id}", response_model=schemas.PregnancyResponse)
def update_pregnancy(pregnancy_id: uuid.UUID, payload: schemas.PregnancyUpdate, db: Session = Depends(get_db)):
    try:
        return service.update_pregnancy(db, pregnancy_id, payload)
    except ValueError as val_error:
        raise HTTPException(status_code=404, detail=str(val_error))
