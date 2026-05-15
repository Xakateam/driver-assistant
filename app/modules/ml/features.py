from app.core.store import store


def build_user_features(user_id: str) -> dict[str, float]:
    trips = store.list_trips(user_id)
    balance = store.get_balance(user_id)
    trip_count = len(trips)
    total_spend = sum(trip.amount for trip in trips)
    return {
        "monthly_spend": round(total_spend, 2),
        "trip_count": float(trip_count),
        "avg_check": round(total_spend / trip_count, 2) if trip_count else 0,
        "balance": balance,
        "late_payments": 0,
    }
