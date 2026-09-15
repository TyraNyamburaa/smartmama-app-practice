from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from smartmama.models.user_model import User
from smartmama.models.person_model import Person
from smartmama.models.token_model import RevokedToken
from smartmama.models.token_model import ResetOTP

class UserRepository:
    def __init__(self):
        self.model = User

    def get(self, db: Session, user_id: UUID) -> User | None:
        return db.query(self.model).filter(self.model.user_id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.query(self.model).filter(self.model.email == email).first()

    def create_user_and_person(self, db: Session, person_data: dict, user_data: dict) -> User:
        db_person = Person(**person_data)
        db.add(db_person)
        db.flush()  
        db_user = self.model(person_id=db_person.person_id, **user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def revoke_token(self, db: Session, token_str: str) -> None:
        db.add(RevokedToken(token=token_str))
        db.commit()

user_repository = UserRepository()

class OTPRepository:
    def create_otp(self, db: Session, user_id: UUID, otp_code: str, expires_at: datetime):
        otp = ResetOTP(
            user_id=user_id,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.add(otp)
        db.commit()
        db.refresh(otp)
        return otp

    def get_valid_otp(self, db: Session, user_id: UUID, otp_code: str):
        return (
            db.query(ResetOTP)
            .filter(
                ResetOTP.user_id == user_id,
                ResetOTP.otp_code == otp_code,
                ResetOTP.is_used == False,
                ResetOTP.expires_at > datetime.utcnow()
            )
            .first()
        )

    def mark_used(self, db: Session, otp: ResetOTP):
        otp.is_used = True
        db.commit()

otp_repository = OTPRepository()