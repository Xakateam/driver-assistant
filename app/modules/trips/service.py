from datetime import UTC, date, datetime, time

from app.core.store import TripRecord, store


def _serialize_trip(trip: TripRecord) -> dict[str, object]:
    return {
        "id": trip.id,
        "vehicle_id": trip.vehicle_id,
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
    trips = store.list_trips(user_id, vehicle_id, started_from, started_to)
    return [_serialize_trip(trip) for trip in trips]


def get_trip(user_id: str, trip_id: str) -> dict[str, object] | None:
    trip = store.trips.get(trip_id)
    if not trip or trip.user_id != user_id:
        return None
    return _serialize_trip(trip)
