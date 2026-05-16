from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUserDep
from app.api.v1.schemas import TripOut
from app.modules.trips import service

router = APIRouter()


@router.get("", response_model=list[TripOut])
async def get_trips(
    current_user: CurrentUserDep,
    vehicle_id: str | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> list[TripOut]:
    return service.list_trips(
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{trip_id}", response_model=TripOut)
async def get_trip(
    trip_id: str,
    current_user: CurrentUserDep,
) -> TripOut:
    trip = service.get_trip(current_user.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip
