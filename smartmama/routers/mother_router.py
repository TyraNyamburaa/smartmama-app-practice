from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from smartmama.schemas.mother_schema import (
    MotherCreate,
    MotherResponse,
    MotherUpdate
)
from smartmama.security import require_chv, require_supervisor
from smartmama.services import mother_service
from smartmama.repositories import mother_repository
from smartmama.models.mother_model import Mother

router = APIRouter(
    prefix="/mothers",
    tags=["Mothers"]
)

@router.post(
    "",
    response_model=MotherResponse,
    status_code=status.HTTP_201_CREATED
)
def create_mother_profile(
    data: MotherCreate,
    db: Session = Depends(get_db),
    current_chv = Depends(require_chv)
):
    return mother_service.register_mother(
        db,
        data,
        current_chv.chv_id
    )


@router.get(
    "",
    response_model=list[MotherResponse]
)
def get_mothers(
    db: Session = Depends(get_db),
    current_chv = Depends(require_chv)
):
    return mother_service.get_mothers(
        db,
        current_chv.chv_id
    )


@router.get(
    "/{mother_id}",
    response_model=MotherResponse
)
def get_mother_profile(
    mother_id: UUID,
    db: Session = Depends(get_db),
    current_chv = Depends(require_chv)
):
    return mother_service.get_mother(
        db,
        mother_id,
        current_chv.chv_id
    )


@router.patch(
    "/{mother_id}",
    response_model=MotherResponse
)
def update_mother_profile(
    mother_id: UUID,
    data: MotherUpdate,
    db: Session = Depends(get_db),
    current_chv = Depends(require_chv)
):
    return mother_service.update_mother(
        db,
        mother_id,
        current_chv.chv_id,
        data
    )

@router.patch(
    "/{mother_id}/reassign",
    response_model=MotherResponse
)
def reassign_mother_to_chv(
    mother_id: UUID,
    new_chv_id: UUID,
    db: Session = Depends(get_db),
    current_supervisor = Depends(require_supervisor)
):
    mother = db.query(Mother).filter(Mother.mother_id == mother_id).first()
    if not mother:
        raise HTTPException(status_code=404, detail="Mother not found")
      
    return mother_service.reassign_mother(
        db,
        mother,
        new_chv_id,
        current_supervisor.user_id
    )
