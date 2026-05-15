from app.core.store import TransactionRecord, TransactionType, store
from app.modules.notifications.service import notification_service


def _serialize_transaction(transaction: TransactionRecord) -> dict[str, object]:
    return {
        "id": transaction.id,
        "type": transaction.type,
        "amount": transaction.amount,
        "currency": "RUB",
        "description": transaction.description,
        "created_at": transaction.created_at.isoformat(),
    }


def get_balance(user_id: str) -> dict[str, object]:
    balance = store.get_balance(user_id)
    avg_daily_spend = _average_daily_spend(user_id)
    forecast_days_left = int(balance // avg_daily_spend) if avg_daily_spend > 0 else None
    return {
        "amount": balance,
        "currency": "RUB",
        "forecast_days_left": forecast_days_left,
    }


def top_up(user_id: str, amount: float, payment_method: str) -> dict[str, object]:
    transaction = store.create_transaction(
        user_id=user_id,
        type=TransactionType.TOP_UP,
        amount=amount,
        description=f"Top-up via {payment_method}",
    )
    notification_service.create_notification(
        user_id=user_id,
        type="topup_success",
        title="Баланс пополнен",
        body=f"На счет зачислено {amount:.0f} ₽.",
        deep_link="driverassistant://balance",
        metadata={"amount": amount, "payment_method": payment_method},
    )
    return {
        "status": "success",
        "balance": get_balance(user_id),
        "transaction": _serialize_transaction(transaction),
    }


def list_transactions(user_id: str) -> list[dict[str, object]]:
    return [
        _serialize_transaction(transaction)
        for transaction in store.list_transactions(user_id)
    ]


def _average_daily_spend(user_id: str) -> float:
    trips = store.list_trips(user_id)
    if not trips:
        return 0
    return round(sum(trip.amount for trip in trips) / max(len({trip.started_at.date() for trip in trips}), 1), 2)
