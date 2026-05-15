from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUserDep
from app.modules.trips import service

router = APIRouter()


@router.get("")
async def get_trips(
    current_user: CurrentUserDep,
    vehicle_id: str | None = None,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
) -> list[dict[str, object]]:
    return service.list_trips(
        user_id=current_user.id,
        vehicle_id=vehicle_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{trip_id}")
async def get_trip(
    trip_id: str,
    current_user: CurrentUserDep,
) -> dict[str, object]:
    trip = service.get_trip(current_user.id, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip
