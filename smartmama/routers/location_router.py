from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from smartmama.schemas.location_schema import LocationCreate, LocationResponse
from smartmama.services.location_service import (
    save_mother_location,
    fetch_all_locations,
    fetch_location_by_id,
    modify_mother_location,
    remove_location_record
)
from uuid import UUID

router = APIRouter(prefix="/locations", tags=["Maternal Map Locations"])

@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)):
    return save_mother_location(db=db, payload=payload)

@router.get("/", response_model=List[LocationResponse])
def read_all_locations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return fetch_all_locations(db=db, skip=skip, limit=limit)

@router.get("/{location_id}", response_model=LocationResponse)
def read_location_by_id(location_id: UUID, db: Session = Depends(get_db)):
    return fetch_location_by_id(db=db, location_id=location_id)

@router.patch("/{location_id}", response_model=LocationResponse)
def update_location(location_id: UUID, payload: LocationCreate, db: Session = Depends(get_db)):
    return modify_mother_location(db=db, location_id=location_id, payload=payload)

@router.delete("/{location_id}", status_code=status.HTTP_200_OK)
def delete_location(location_id: UUID, db: Session = Depends(get_db)):
    return remove_location_record(db=db, location_id=location_id)
