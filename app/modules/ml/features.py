from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.models import AutopaySettingORM, TransactionORM, TripORM, UserORM


DELAYED_PAYMENT_STATUSES = {"debt", "overdue", "delayed"}


def build_cluster_features(user_id: str, db: Session | None = None) -> dict[str, float]:
    if db is None:
        with SessionLocal() as session:
            return build_cluster_features(user_id, session)

    trips = _load_trips(db, user_id)
    trip_count = len(trips)
    total_spent = sum(trip.amount for trip in trips)
    weekend_count = sum(1 for trip in trips if trip.started_at.weekday() >= 5)
    delayed_count = sum(1 for trip in trips if trip.status in DELAYED_PAYMENT_STATUSES)

    return {
        "trip_frequency": float(trip_count),
        "avg_check": round(total_spent / trip_count, 2) if trip_count else 0.0,
        "weekend_share": round(weekend_count / trip_count, 4) if trip_count else 0.0,
        "is_delayed_payment": round(delayed_count / trip_count, 4)
        if trip_count
        else 0.0,
    }


def build_spend_features(
    user_id: str,
    ml_cluster_id: int | None,
    db: Session | None = None,
) -> dict[str, float]:
    if db is None:
        with SessionLocal() as session:
            return build_spend_features(user_id, ml_cluster_id, session)

    period_start = datetime.now(UTC) - timedelta(days=30)
    trips = db.scalars(
        select(TripORM).where(
            TripORM.user_id == user_id,
            TripORM.started_at >= period_start,
        )
    ).all()
    return {
        "trips_count": float(len(trips)),
        "total_spent": round(sum(trip.amount for trip in trips), 2),
        "ml_cluster_id": float(ml_cluster_id if ml_cluster_id is not None else 0),
    }


def build_recommendation_features(
    user_id: str,
    category_id: int,
    *,
    ml_cluster_id: int | None = None,
    predicted_spend_next_month: float | None = None,
    db: Session | None = None,
) -> dict[str, float]:
    if db is None:
        with SessionLocal() as session:
            return build_recommendation_features(
                user_id,
                category_id,
                ml_cluster_id=ml_cluster_id,
                predicted_spend_next_month=predicted_spend_next_month,
                db=session,
            )

    user = db.get(UserORM, user_id)
    balance = _current_balance(db, user_id)
    debt_amount = _debt_amount(db, user_id)

    cluster_id = ml_cluster_id
    if cluster_id is None and user is not None:
        cluster_id = user.ml_cluster_id

    predicted_spend = predicted_spend_next_month
    if predicted_spend is None and user is not None:
        predicted_spend = user.predicted_spend_next_month

    return {
        "current_balance": balance,
        "debt_amount": debt_amount,
        "ml_cluster_id": float(cluster_id if cluster_id is not None else 0),
        "predicted_spend_next_month": round(float(predicted_spend or 0), 2),
        "category_id": float(category_id),
    }


def build_user_features(user_id: str) -> dict[str, float]:
    cluster_features = build_cluster_features(user_id)
    recommendation_features = build_recommendation_features(user_id, category_id=5)
    return {
        "monthly_spend": recommendation_features["predicted_spend_next_month"],
        "trip_count": cluster_features["trip_frequency"],
        "avg_check": cluster_features["avg_check"],
        "balance": recommendation_features["current_balance"],
        "late_payments": cluster_features["is_delayed_payment"],
    }


def get_favorite_route_name(user_id: str, db: Session | None = None) -> str | None:
    if db is None:
        with SessionLocal() as session:
            return get_favorite_route_name(user_id, session)

    trips = _load_trips(db, user_id)
    if not trips:
        return None

    routes = Counter(
        f"{trip.road_name}: {trip.entry_point} -> {trip.exit_point}" for trip in trips
    )
    return routes.most_common(1)[0][0]


def has_autopay(user_id: str, db: Session | None = None) -> bool:
    if db is None:
        with SessionLocal() as session:
            return has_autopay(user_id, session)

    autopay = db.get(AutopaySettingORM, user_id)
    return bool(autopay and autopay.enabled)


def _load_trips(db: Session, user_id: str) -> list[TripORM]:
    return list(db.scalars(select(TripORM).where(TripORM.user_id == user_id)).all())


def _current_balance(db: Session, user_id: str) -> float:
    transactions = db.scalars(
        select(TransactionORM).where(TransactionORM.user_id == user_id)
    ).all()
    return round(sum(transaction.amount for transaction in transactions), 2)


def _debt_amount(db: Session, user_id: str) -> float:
    trips = db.scalars(
        select(TripORM).where(
            TripORM.user_id == user_id,
            TripORM.status.in_(DELAYED_PAYMENT_STATUSES),
        )
    ).all()
    return round(sum(trip.amount for trip in trips), 2)
