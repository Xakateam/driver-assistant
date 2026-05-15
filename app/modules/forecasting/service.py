from datetime import UTC, datetime

from app.core.store import store


def get_monthly_forecast(user_id: str) -> dict[str, object]:
    now = datetime.now(UTC)
    month_trips = [
        trip
        for trip in store.list_trips(user_id)
        if trip.started_at.year == now.year and trip.started_at.month == now.month
    ]
    spent_so_far = round(sum(trip.amount for trip in month_trips), 2)
    active_days = max(now.day, 1)
    avg_daily_spend = spent_so_far / active_days if active_days else 0
    days_in_demo_month = 30
    expected = round(avg_daily_spend * days_in_demo_month, 2)
    remaining = max(round(expected - spent_so_far, 2), 0)
    balance = store.get_balance(user_id)
    return {
        "month_expected_spend": expected,
        "remaining_month_spend": remaining,
        "low_balance_risk": balance < remaining,
    }
