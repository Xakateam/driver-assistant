from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import TransactionORM, TripORM


def build_user_features(user_id: str) -> dict[str, float]:
    with SessionLocal() as db:
        trips = db.scalars(select(TripORM).where(TripORM.user_id == user_id)).all()
        transactions = db.scalars(
            select(TransactionORM).where(TransactionORM.user_id == user_id)
        ).all()
    balance = round(sum(transaction.amount for transaction in transactions), 2)
    trip_count = len(trips)
    total_spend = sum(trip.amount for trip in trips)
    late_payments = len([trip for trip in trips if trip.status == "debt"])
    return {
        "monthly_spend": round(total_spend, 2),
        "trip_count": float(trip_count),
        "avg_check": round(total_spend / trip_count, 2) if trip_count else 0,
        "balance": balance,
        "late_payments": float(late_payments),
    }
