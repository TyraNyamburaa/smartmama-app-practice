from uuid import UUID
from sqlalchemy.orm import Session
from ..models.location_model import Location

def create_location(db: Session, db_location: Location) -> Location:
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_all_locations(db: Session, skip: int = 0, limit: int = 100) -> list[Location]:
    return db.query(Location).offset(skip).limit(limit).all()

def get_location_by_id(db: Session, location_id: UUID) -> Location | None:
    return db.query(Location).filter(Location.location_id == location_id).first()

def delete_location_record(db: Session, db_location: Location) -> None:
    db.delete(db_location)
    db.commit()
