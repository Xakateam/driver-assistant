from fastapi import APIRouter, HTTPException, status

from app.modules.auth.dependencies import CurrentUserDep
from app.modules.vehicles.schemas import VehicleCreateIn, VehicleOut, VehicleUpdateIn
from app.modules.vehicles.service import vehicle_service

router = APIRouter()


@router.get("", response_model=list[VehicleOut])
async def get_vehicles(current_user: CurrentUserDep) -> list[VehicleOut]:
    return [
        VehicleOut.model_validate(vehicle)
        for vehicle in vehicle_service.list_for_user(current_user.id)
    ]


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreateIn,
    current_user: CurrentUserDep,
) -> VehicleOut:
    vehicle = vehicle_service.create_for_user(current_user.id, payload)
    return VehicleOut.model_validate(vehicle)


@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: str, current_user: CurrentUserDep) -> VehicleOut:
    vehicle = vehicle_service.get_for_user(current_user.id, vehicle_id)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    return VehicleOut.model_validate(vehicle)


@router.patch("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdateIn,
    current_user: CurrentUserDep,
) -> VehicleOut:
    vehicle = vehicle_service.update_for_user(current_user.id, vehicle_id, payload)
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    return VehicleOut.model_validate(vehicle)


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    current_user: CurrentUserDep,
) -> dict[str, str]:
    was_deleted = vehicle_service.delete_for_user(current_user.id, vehicle_id)
    if not was_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    return {"id": vehicle_id, "status": "deleted"}
