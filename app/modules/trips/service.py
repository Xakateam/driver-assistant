from datetime import UTC, date, datetime, time

from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import TripORM


def _serialize_trip(trip: TripORM) -> dict[str, object]:
    return {
        "id": trip.id,
        "vehicle_id": trip.vehicle_id,
        "road_name": trip.road_name,
        "started_at": trip.started_at.isoformat(),
        "finished_at": trip.finished_at.isoformat(),
        "entry_point": trip.entry_point,
        "exit_point": trip.exit_point,
        "distance_km": trip.distance_km,
        "amount": trip.amount,
        "currency": "RUB",
        "status": trip.status,
    }


def list_trips(
    user_id: str,
    vehicle_id: str | None,
    date_from: date | None,
    date_to: date | None,
) -> list[dict[str, object]]:
    started_from = (
        datetime.combine(date_from, time.min, tzinfo=UTC) if date_from else None
    )
    started_to = datetime.combine(date_to, time.max, tzinfo=UTC) if date_to else None
    with SessionLocal() as db:
        query = select(TripORM).where(TripORM.user_id == user_id)
        if vehicle_id:
            query = query.where(TripORM.vehicle_id == vehicle_id)
        if started_from:
            query = query.where(TripORM.started_at >= started_from)
        if started_to:
            query = query.where(TripORM.started_at <= started_to)
        trips = db.scalars(query.order_by(TripORM.started_at.desc())).all()
        return [_serialize_trip(trip) for trip in trips]


def get_trip(user_id: str, trip_id: str) -> dict[str, object] | None:
    with SessionLocal() as db:
        trip = db.get(TripORM, trip_id)
        if not trip or trip.user_id != user_id:
            return None
        return _serialize_trip(trip)
