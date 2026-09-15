import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from smartmama.models.location_model import Location
from smartmama.schemas.location_schema import LocationCreate
from smartmama.repositories.location_repository import (
    create_location,
    get_all_locations,
    get_location_by_id,
    delete_location_record
)

base_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")

LOCATIONIQ_API_TOKEN = os.getenv("LOCATIONIQ_API_TOKEN")


def geocode_address_to_coordinates(address_text: str) -> tuple[float, float]:
    url = "https://locationiq.com/v1/search.php"
    params = {
        "key": LOCATIONIQ_API_TOKEN,
        "q": address_text,
        "format": "json",
        "limit": 1
    }
    try:
        response = requests.get(url, params=params, timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="External mapping engine authentication failure.")
        geo_data = response.json()
        return float(geo_data[0]["lat"]), float(geo_data[0]["lon"])
    except Exception:
        return -1.2921, 36.8219


def save_mother_location(db: Session, payload: LocationCreate) -> Location:
    lat, lon = geocode_address_to_coordinates(payload.location_name)

    db_location = Location(
        location_name=payload.location_name,
        latitude=lat,
        longitude=lon
    )
    return create_location(db=db, db_location=db_location)


def fetch_all_locations(db: Session, skip: int = 0, limit: int = 100) -> list[Location]:
    return get_all_locations(db=db, skip=skip, limit=limit)


def fetch_location_by_id(db: Session, location_id: UUID) -> Location:
    db_location = get_location_by_id(db=db, location_id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location record profile not found"
        )
    return db_location


def modify_mother_location(db: Session, location_id: UUID, payload: LocationCreate) -> Location:
    db_location = fetch_location_by_id(db, location_id)

    if db_location.location_name != payload.location_name:
        lat, lon = geocode_address_to_coordinates(payload.location_name)
        db_location.latitude = lat
        db_location.longitude = lon
        db_location.location_name = payload.location_name

    db.commit()
    db.refresh(db_location)
    return db_location


def remove_location_record(db: Session, location_id: UUID) -> dict:
    db_location = fetch_location_by_id(db, location_id)
    delete_location_record(db=db, db_location=db_location)
    return {"status": "success", "detail": "Maternal map tracking record dropped successfully"}
