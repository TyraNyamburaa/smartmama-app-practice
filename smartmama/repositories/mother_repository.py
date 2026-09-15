from uuid import UUID
from sqlalchemy.orm import Session
from smartmama.models.mother_model import Mother
from smartmama.models.person_model import Person


class MotherRepository:
    def __init__(self):
        self.model = Mother

    def get_mother_profile(self, db: Session, mother_id: UUID, chv_id: UUID):
        return db.query(self.model).filter(
            self.model.mother_id == mother_id,
            self.model.chv_id == chv_id
        ).first()

    def get_mothers_profile(self, db: Session, chv_id: UUID):
        return db.query(self.model).filter(
            self.model.chv_id == chv_id
        ).all()

    def create_mother_profile(self, db: Session, person_data: dict, mother_data:dict) -> Mother:
        person = Person(**person_data)
        db.add(person)
        db.flush()
        mother = Mother(person_id=person.person_id, **mother_data)
        db.add(mother)
        db.commit()
        db.refresh(mother)
        return mother

    def update_mother_profile(self, db: Session, mother: Mother, data: dict):
        for field, value in data.items():
            if hasattr(mother, field):
                setattr(mother, field, value)
        db.commit()
        db.refresh(mother)
        return mother

    def delete_mother_profile(self, db: Session, mother: Mother) -> None:
        db.delete(mother)
        db.commit()
    
    def get_mother_by_id(self, db: Session, mother_id: UUID):
        return db.query(self.model).filter(self.model.mother_id == mother_id).first()


mother_repository = MotherRepository()












