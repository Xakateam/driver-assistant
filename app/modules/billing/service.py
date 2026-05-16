from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import AutopaySettingORM, TransactionORM, TripORM
from app.modules.notifications.service import notification_service


def _serialize_transaction(transaction: TransactionORM) -> dict[str, object]:
    return {
        "id": transaction.id,
        "type": transaction.type,
        "amount": transaction.amount,
        "currency": "RUB",
        "description": transaction.description,
        "created_at": transaction.created_at.isoformat(),
    }


def get_balance(user_id: str) -> dict[str, object]:
    balance = _balance_amount(user_id)
    avg_daily_spend = _average_daily_spend(user_id)
    forecast_days_left = int(balance // avg_daily_spend) if avg_daily_spend > 0 else None
    return {
        "amount": balance,
        "currency": "RUB",
        "forecast_days_left": forecast_days_left,
    }


def top_up(user_id: str, amount: float, payment_method: str) -> dict[str, object]:
    with SessionLocal() as db:
        transaction = TransactionORM(
            user_id=user_id,
            type="top_up",
            amount=amount,
            description=f"Top-up via {payment_method}",
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

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
    with SessionLocal() as db:
        transactions = db.scalars(
            select(TransactionORM)
            .where(TransactionORM.user_id == user_id)
            .order_by(TransactionORM.created_at.desc())
        ).all()
        return [_serialize_transaction(transaction) for transaction in transactions]


def get_autopay(user_id: str) -> dict[str, object]:
    with SessionLocal() as db:
        autopay = db.get(AutopaySettingORM, user_id)
        if autopay is None:
            autopay = AutopaySettingORM(user_id=user_id)
            db.add(autopay)
            db.commit()
            db.refresh(autopay)
        return _serialize_autopay(autopay)


def update_autopay(
    user_id: str,
    *,
    enabled: bool | None,
    threshold_amount: float | None,
    top_up_amount: float | None,
    payment_method: str | None,
) -> dict[str, object]:
    with SessionLocal() as db:
        autopay = db.get(AutopaySettingORM, user_id)
        if autopay is None:
            autopay = AutopaySettingORM(user_id=user_id)
            db.add(autopay)
        if enabled is not None:
            autopay.enabled = enabled
        if threshold_amount is not None:
            autopay.threshold_amount = threshold_amount
        if top_up_amount is not None:
            autopay.top_up_amount = top_up_amount
        if payment_method is not None:
            autopay.payment_method = payment_method
        autopay.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(autopay)
        return _serialize_autopay(autopay)


def list_debts(user_id: str) -> list[dict[str, object]]:
    with SessionLocal() as db:
        trips = db.scalars(
            select(TripORM)
            .where(TripORM.user_id == user_id, TripORM.status == "debt")
            .order_by(TripORM.started_at.desc())
        ).all()
        return [
            {
                "id": trip.id,
                "trip_id": trip.id,
                "road_name": trip.road_name,
                "amount": trip.amount,
                "currency": "RUB",
                "status": "overdue",
                "due_text": "Оплатите до 13 июня — после будет штраф",
                "deep_link": f"driverassistant://debts/{trip.id}",
                "created_at": trip.started_at.isoformat(),
            }
            for trip in trips
        ]


def pay_debt(user_id: str, debt_id: str) -> dict[str, object] | None:
    with SessionLocal() as db:
        trip = db.get(TripORM, debt_id)
        if trip is None or trip.user_id != user_id or trip.status != "debt":
            return None

        transaction = TransactionORM(
            user_id=user_id,
            type="debt",
            amount=-float(trip.amount),
            description=f"Debt payment for {trip.entry_point} -> {trip.exit_point}",
        )
        trip.status = "paid"
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

    notification_service.create_notification(
        user_id=user_id,
        type="debt_paid",
        title="Задолженность погашена",
        body=f"Оплата поездки {debt_id[:8]} на {transaction.amount * -1:.0f} ₽ прошла.",
        deep_link="driverassistant://debts",
        metadata={"debt_id": debt_id, "amount": abs(transaction.amount)},
    )
    return {
        "status": "paid",
        "debt_id": debt_id,
        "balance": get_balance(user_id),
        "debts_summary": get_debt_summary(user_id),
        "transaction": _serialize_transaction(transaction),
    }


def get_debt_summary(user_id: str) -> dict[str, object]:
    debts = list_debts(user_id)
    total_amount = round(sum(float(debt["amount"]) for debt in debts), 2)
    return {
        "count": len(debts),
        "amount": total_amount,
        "currency": "RUB",
        "has_overdues": bool(debts),
    }


def _balance_amount(user_id: str) -> float:
    with SessionLocal() as db:
        transactions = db.scalars(
            select(TransactionORM).where(TransactionORM.user_id == user_id)
        ).all()
        return round(sum(item.amount for item in transactions), 2)


def _serialize_autopay(autopay: AutopaySettingORM) -> dict[str, object]:
    return {
        "enabled": autopay.enabled,
        "threshold_amount": autopay.threshold_amount,
        "top_up_amount": autopay.top_up_amount,
        "payment_method": autopay.payment_method,
        "updated_at": autopay.updated_at.isoformat(),
    }


def _average_daily_spend(user_id: str) -> float:
    with SessionLocal() as db:
        trips = db.scalars(select(TripORM).where(TripORM.user_id == user_id)).all()
        if not trips:
            return 0
        active_days = max(len({trip.started_at.date() for trip in trips}), 1)
        return round(sum(trip.amount for trip in trips) / active_days, 2)
