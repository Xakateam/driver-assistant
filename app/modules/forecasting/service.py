from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import TransactionORM, TripORM, UserORM


def get_monthly_forecast(user_id: str) -> dict[str, object]:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        month_trips = db.scalars(
            select(TripORM).where(
                TripORM.user_id == user_id,
                TripORM.started_at >= datetime(now.year, now.month, 1, tzinfo=UTC),
            )
        ).all()
        transactions = db.scalars(
            select(TransactionORM).where(TransactionORM.user_id == user_id)
        ).all()
        user = db.get(UserORM, user_id)

    spent_so_far = round(sum(trip.amount for trip in month_trips), 2)
    avg_daily_spend = spent_so_far / max(now.day, 1)
    if user and user.predicted_spend_next_month is not None:
        expected = round(user.predicted_spend_next_month, 2)
        source = "ml"
    else:
        expected = round(avg_daily_spend * 30, 2)
        source = "heuristic"
    remaining = max(round(expected - spent_so_far, 2), 0)
    balance = round(sum(transaction.amount for transaction in transactions), 2)
    return {
        "month_expected_spend": expected,
        "remaining_month_spend": remaining,
        "low_balance_risk": balance < remaining,
        "source": source,
    }
