from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import UserORM


@dataclass(frozen=True)
class User:
    id: str
    phone: str
    segment: str = "commuter"
    ml_cluster_id: int | None = None
    ml_cluster_name: str | None = None
    predicted_spend_next_month: float | None = None
    favorite_route_name: str | None = None
    ml_model_version: str | None = None
    ml_updated_at: str | None = None


def _to_user(user: UserORM) -> User:
    return User(
        id=user.id,
        phone=user.phone,
        segment=user.segment,
        ml_cluster_id=user.ml_cluster_id,
        ml_cluster_name=user.ml_cluster_name,
        predicted_spend_next_month=user.predicted_spend_next_month,
        favorite_route_name=user.favorite_route_name,
        ml_model_version=user.ml_model_version,
        ml_updated_at=user.ml_updated_at.isoformat() if user.ml_updated_at else None,
    )


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
