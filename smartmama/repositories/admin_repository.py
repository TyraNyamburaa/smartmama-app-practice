from uuid import UUID
from sqlalchemy.orm import Session
from smartmama.models.admin_model import Admin

class AdminRepository:
    def __init__(self):
        self.model = Admin

    def get_admin_profile(self, db: Session, admin_id: UUID) -> Admin | None:
        
        return (
            db.query(self.model)
            .filter(self.model.admin_id == admin_id)
            .first()
        )

    def get_admin_profile_by_user_id(self, db: Session, user_id: UUID) -> Admin | None:
        
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .first()
        )

    def create_admin_profile(self, db: Session, user_id: UUID, is_superadmin: bool = False) -> Admin:
        
        db_admin = self.model(
            user_id=user_id,
            is_superadmin=is_superadmin
        )
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        return db_admin

    def update_admin_profile(self, db: Session, admin: Admin, data: dict) -> Admin:
        
        for key, value in data.items():
            if hasattr(admin, key):
                setattr(admin, key, value)
        db.commit()
        db.refresh(admin)
        return admin

    def delete_admin_profile(self, db: Session, admin: Admin) -> Admin:
        
        if admin.user:
            admin.user.is_active = False
            db.commit()
            db.refresh(admin)
        return admin

    def list_admins(self, db: Session, skip: int = 0, limit: int = 20) -> list[Admin]:
        return (
            db.query(self.model)
            .order_by(self.model.admin_id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
   
    def count_admins(self, db: Session) -> int:
        return db.query(self.model).count()

admin_repository = AdminRepository()
