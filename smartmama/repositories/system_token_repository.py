from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from smartmama.models.token_model import SystemToken
from smartmama.security import hash_token


class SystemTokenRepository:
    def __init__(self):
        self.model = SystemToken

    def create_token(
        self, 
        db: Session, 
        token_hash: str, 
        token_type: str, 
        target_person_id: UUID, 
        expires_at: datetime
    ) -> SystemToken:
        
        db_token = self.model(
            token_hash=token_hash,
            token_type=token_type,
            target_person_id=target_person_id,
            status="SENT",
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    def get_valid_token(self, db: Session, raw_token: str) -> SystemToken | None:
        
        now = datetime.now(timezone.utc)
        return (
            db.query(self.model)
            .filter(
                self.model.token_hash == hash_token(raw_token),
                self.model.status == "SENT",
                self.model.expires_at > now
            )
            .first()
        )

    def update_token_status(self, db: Session, token: SystemToken, new_status: str) -> SystemToken:
        
        token.status = new_status
        db.commit()
        db.refresh(token)
        return token


system_token_repository = SystemTokenRepository()
