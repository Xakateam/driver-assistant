from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from app.modules.vehicles.schemas import VehicleCreateIn, VehicleUpdateIn


@dataclass
class Vehicle:
    id: str
    user_id: str
    plate_number: str
    name: str | None
    is_primary: bool


class VehicleService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._vehicles_by_id: dict[str, Vehicle] = {}

    def list_for_user(self, user_id: str) -> list[Vehicle]:
        with self._lock:
            return [
                vehicle
                for vehicle in self._vehicles_by_id.values()
                if vehicle.user_id == user_id
            ]

    def create_for_user(self, user_id: str, payload: VehicleCreateIn) -> Vehicle:
        with self._lock:
            if payload.is_primary:
                self._clear_primary(user_id)

            vehicle = Vehicle(
                id=str(uuid4()),
                user_id=user_id,
                plate_number=payload.plate_number,
                name=payload.name,
                is_primary=payload.is_primary,
            )
            self._vehicles_by_id[vehicle.id] = vehicle
            return vehicle

    def get_for_user(self, user_id: str, vehicle_id: str) -> Vehicle | None:
        with self._lock:
            vehicle = self._vehicles_by_id.get(vehicle_id)
            if vehicle is None or vehicle.user_id != user_id:
                return None
            return vehicle

    def update_for_user(
        self,
        user_id: str,
        vehicle_id: str,
        payload: VehicleUpdateIn,
    ) -> Vehicle | None:
        with self._lock:
            vehicle = self.get_for_user(user_id, vehicle_id)
            if vehicle is None:
                return None

            update_data = payload.model_dump(exclude_unset=True)
            if update_data.get("is_primary") is True:
                self._clear_primary(user_id)

            for field_name, value in update_data.items():
                setattr(vehicle, field_name, value)

            return vehicle

    def delete_for_user(self, user_id: str, vehicle_id: str) -> bool:
        with self._lock:
            vehicle = self.get_for_user(user_id, vehicle_id)
            if vehicle is None:
                return False

            del self._vehicles_by_id[vehicle_id]
            return True

    def _clear_primary(self, user_id: str) -> None:
        for vehicle in self._vehicles_by_id.values():
            if vehicle.user_id == user_id:
                vehicle.is_primary = False


vehicle_service = VehicleService()
