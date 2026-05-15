from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import TransactionORM, TripORM


def get_feed(user_id: str, kind: str = "all", limit: int = 20, offset: int = 0) -> dict[str, object]:
    items: list[dict[str, object]] = []
    normalized_kind = kind.lower()

    if normalized_kind in {"all", "trips", "overdues"}:
        items.extend(_trip_items(user_id, normalized_kind))
    if normalized_kind in {"all", "payments"}:
        items.extend(_payment_items(user_id))

    items = sorted(items, key=lambda item: str(item["occurred_at"]), reverse=True)
    return {
        "items": items[offset : offset + limit],
        "limit": limit,
        "offset": offset,
        "total": len(items),
    }


def _trip_items(user_id: str, kind: str) -> list[dict[str, object]]:
    with SessionLocal() as db:
        query = select(TripORM).where(TripORM.user_id == user_id)
        if kind == "overdues":
            query = query.where(TripORM.status == "debt")
        trips = db.scalars(query).all()
    return [
        {
            "id": trip.id,
            "kind": "overdue" if trip.status == "debt" else "trip",
            "title": f"{trip.entry_point} → {trip.exit_point}",
            "subtitle": f"{trip.road_name} · {trip.distance_km:.0f} км",
            "amount": -trip.amount,
            "currency": "RUB",
            "status": trip.status,
            "occurred_at": trip.started_at.isoformat(),
            "deep_link": f"driverassistant://trips/{trip.id}",
            "metadata": {
                "road_name": trip.road_name,
                "entry_point": trip.entry_point,
                "exit_point": trip.exit_point,
            },
        }
        for trip in trips
    ]


def _payment_items(user_id: str) -> list[dict[str, object]]:
    with SessionLocal() as db:
        payments = db.scalars(
            select(TransactionORM).where(
                TransactionORM.user_id == user_id,
                TransactionORM.type == "top_up",
            )
        ).all()
    return [
        {
            "id": payment.id,
            "kind": "payment",
            "title": "Пополнение баланса",
            "subtitle": payment.description,
            "amount": payment.amount,
            "currency": "RUB",
            "status": "success",
            "occurred_at": payment.created_at.isoformat(),
            "deep_link": "driverassistant://balance",
            "metadata": {"type": payment.type},
        }
        for payment in payments
    ]
