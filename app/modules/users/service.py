from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import UserORM


@dataclass(frozen=True)
class User:
    id: str
    phone: str
    segment: str = "commuter"


def _to_user(user: UserORM) -> User:
    return User(id=user.id, phone=user.phone, segment=user.segment)


class UserService:
    def get_or_create_by_phone(self, phone: str) -> User:
        normalized_phone = phone.strip()
        with SessionLocal() as db:
            user = db.scalar(select(UserORM).where(UserORM.phone == normalized_phone))
            if user is None:
                user = UserORM(phone=normalized_phone)
                db.add(user)
                db.commit()
                db.refresh(user)
            return _to_user(user)

    def get_by_id(self, user_id: str) -> User | None:
        with SessionLocal() as db:
            user = db.get(UserORM, user_id)
            return _to_user(user) if user else None


user_service = UserService()
