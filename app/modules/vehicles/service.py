from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import VehicleORM
from app.modules.vehicles.schemas import VehicleCreateIn, VehicleUpdateIn


@dataclass
class Vehicle:
    id: str
    user_id: str
    plate_number: str
    name: str | None
    is_primary: bool


def _to_vehicle(vehicle: VehicleORM) -> Vehicle:
    return Vehicle(
        id=vehicle.id,
        user_id=vehicle.user_id,
        plate_number=vehicle.plate_number,
        name=vehicle.name,
        is_primary=vehicle.is_primary,
    )


class VehicleService:
    def list_for_user(self, user_id: str) -> list[Vehicle]:
        with SessionLocal() as db:
            vehicles = db.scalars(
                select(VehicleORM)
                .where(VehicleORM.user_id == user_id)
                .order_by(VehicleORM.created_at)
            ).all()
            return [_to_vehicle(vehicle) for vehicle in vehicles]

    def create_for_user(self, user_id: str, payload: VehicleCreateIn) -> Vehicle:
        with SessionLocal() as db:
            if payload.is_primary:
                self._clear_primary(db, user_id)
            vehicle = VehicleORM(
                user_id=user_id,
                plate_number=payload.plate_number,
                name=payload.name,
                is_primary=payload.is_primary,
            )
            db.add(vehicle)
            db.commit()
            db.refresh(vehicle)
            return _to_vehicle(vehicle)

    def get_for_user(self, user_id: str, vehicle_id: str) -> Vehicle | None:
        with SessionLocal() as db:
            vehicle = db.get(VehicleORM, vehicle_id)
            if vehicle is None or vehicle.user_id != user_id:
                return None
            return _to_vehicle(vehicle)

    def update_for_user(
        self,
        user_id: str,
        vehicle_id: str,
        payload: VehicleUpdateIn,
    ) -> Vehicle | None:
        with SessionLocal() as db:
            vehicle = db.get(VehicleORM, vehicle_id)
            if vehicle is None or vehicle.user_id != user_id:
                return None
            update_data = payload.model_dump(exclude_unset=True)
            if update_data.get("is_primary") is True:
                self._clear_primary(db, user_id)
            for field_name, value in update_data.items():
                setattr(vehicle, field_name, value)
            db.commit()
            db.refresh(vehicle)
            return _to_vehicle(vehicle)

    def delete_for_user(self, user_id: str, vehicle_id: str) -> bool:
        with SessionLocal() as db:
            vehicle = db.get(VehicleORM, vehicle_id)
            if vehicle is None or vehicle.user_id != user_id:
                return False
            db.delete(vehicle)
            db.commit()
            return True

    @staticmethod
    def _clear_primary(db, user_id: str) -> None:
        vehicles = db.scalars(select(VehicleORM).where(VehicleORM.user_id == user_id))
        for vehicle in vehicles:
            vehicle.is_primary = False


vehicle_service = VehicleService()
