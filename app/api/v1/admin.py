import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.schemas import Metadata
from app.core.config import settings
from app.core.database import SessionLocal, seed_demo_data as seed_db_demo_data
from app.db.models import (
    NotificationORM,
    RecommendationORM,
    TransactionORM,
    TripORM,
    UserORM,
    VehicleORM,
)
from app.modules.billing import service as billing_service
from app.modules.dashboard.service import get_dashboard
from app.modules.ml import service as ml_service
from app.modules.notifications.scheduler import run_notification_tick
from app.modules.notifications.service import notification_service
from app.modules.recommendations.service import recommendation_service
from app.modules.trips.service import list_trips
from app.modules.vehicles.service import vehicle_service
from app.modules.vehicles.schemas import VehicleCreateIn


class AdminNotificationSendIn(BaseModel):
    user_id: str | None = None
    phone: str | None = None
    broadcast: bool = False
    type: str = Field(default="admin_message")
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    deep_link: str | None = None
    metadata: Metadata = Field(default_factory=dict)
    ignore_quiet_hours: bool = False


class AdminUserCreateIn(BaseModel):
    phone: str = Field(examples=["+79990000000"])
    plate_number: str = Field(default="А123ВС777")
    vehicle_name: str = Field(default="Kia Rio")


class AdminTopUpIn(BaseModel):
    amount: float = Field(gt=0, examples=[1000])
    payment_method: str = Field(default="admin")


class AdminTripCreateIn(BaseModel):
    vehicle_id: str | None = None
    road_name: str = Field(default="M-12")
    entry_point: str = Field(default="Ногинск")
    exit_point: str = Field(default="Орехово-Зуево")
    distance_km: float = Field(default=38, gt=0)
    amount: float = Field(default=220, gt=0)
    status: str = Field(default="paid", pattern="^(paid|debt)$")
    started_at: datetime | None = None


class AdminDebtCreateIn(AdminTripCreateIn):
    status: str = Field(default="debt", pattern="^debt$")


class AdminBalanceSetIn(BaseModel):
    amount: float = Field(ge=0)


class AdminScenarioIn(BaseModel):
    phone: str = Field(default="+79990000000")
    reset_notifications: bool = False
    send_push: bool = True


async def require_admin_api_key(
    x_admin_api_key: Annotated[str | None, Header(alias="X-Admin-API-Key")] = None,
) -> None:
    expected_key = _expected_admin_api_key()
    if expected_key is None:
        return
    if x_admin_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
        )


def _expected_admin_api_key() -> str | None:
    return os.getenv("ADMIN_API_KEY") or settings.ADMIN_API_KEY


router = APIRouter(dependencies=[Depends(require_admin_api_key)])


@router.get("/status")
async def admin_status() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/users")
async def list_users(q: str | None = None) -> dict[str, object]:
    with SessionLocal() as db:
        query = select(UserORM).order_by(UserORM.created_at.desc())
        if q:
            query = query.where(UserORM.phone.contains(q))
        users = db.scalars(query.limit(100)).all()
        return {
            "items": [_admin_user_summary(user) for user in users],
            "total": len(users),
        }


@router.post("/users")
async def create_user(payload: AdminUserCreateIn) -> dict[str, object]:
    user = _get_or_create_user(payload.phone)
    _ensure_primary_vehicle(
        user.id,
        plate_number=payload.plate_number,
        vehicle_name=payload.vehicle_name,
    )
    return _get_admin_user_detail(user.id)


@router.get("/users/{user_id}")
async def get_admin_user(user_id: str) -> dict[str, object]:
    return _get_admin_user_detail(user_id)


def _get_admin_user_detail(user_id: str) -> dict[str, object]:
    with SessionLocal() as db:
        user = db.get(UserORM, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "user": _admin_user_summary(user),
            "dashboard": get_dashboard(user.id),
            "transactions": billing_service.list_transactions(user.id)[:20],
            "trips": list_trips(user.id, None, None, None)[:20],
            "debts": billing_service.list_debts(user.id),
            "notifications": notification_service.list_notifications(user_id=user.id)[:20],
            "recommendations": recommendation_service.list_recommendations(
                user_id=user.id,
                include_decided=True,
            ),
        }


@router.post("/users/{user_id}/top-up")
async def admin_top_up(user_id: str, payload: AdminTopUpIn) -> dict[str, object]:
    _ensure_user_exists(user_id)
    return billing_service.top_up(
        user_id=user_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
    )


@router.post("/users/{user_id}/balance")
async def admin_set_balance(
    user_id: str,
    payload: AdminBalanceSetIn,
) -> dict[str, object]:
    _ensure_user_exists(user_id)
    _set_balance(user_id, payload.amount)
    return billing_service.get_balance(user_id)


@router.post("/users/{user_id}/trips")
async def admin_create_trip(
    user_id: str,
    payload: AdminTripCreateIn,
) -> dict[str, object]:
    _ensure_user_exists(user_id)
    return _create_trip(user_id=user_id, payload=payload)


@router.post("/users/{user_id}/debts")
async def admin_create_debt(
    user_id: str,
    payload: AdminDebtCreateIn,
) -> dict[str, object]:
    _ensure_user_exists(user_id)
    return _create_trip(user_id=user_id, payload=payload)


@router.post("/users/{user_id}/ml/recalculate")
async def admin_recalculate_user_ml(user_id: str) -> dict[str, object]:
    result = ml_service.recalculate_user(user_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.post("/demo/scenarios/{scenario}")
async def apply_demo_scenario(
    scenario: str,
    payload: AdminScenarioIn,
) -> dict[str, object]:
    if scenario not in {"low_balance", "debt_user", "heavy_commuter", "weekend_driver"}:
        raise HTTPException(status_code=404, detail="Unknown scenario")

    user = _get_or_create_user(payload.phone)
    vehicle = _ensure_primary_vehicle(user.id)
    if payload.reset_notifications:
        _reset_user_notifications(user.id)

    if scenario == "low_balance":
        _set_balance(user.id, 120)
        _create_trip(user.id, AdminTripCreateIn(vehicle_id=vehicle.id, amount=180))
        notification = _scenario_push(
            user.id,
            enabled=payload.send_push,
            title="Баланс скоро закончится",
            body="На счете осталось около одной поездки. Пополните баланс заранее.",
            deep_link="driverassistant://topup?amount=1000",
            type="low_balance_forecast",
        )
    elif scenario == "debt_user":
        _set_balance(user.id, 700)
        _create_trip(user.id, AdminDebtCreateIn(vehicle_id=vehicle.id, amount=340))
        _create_trip(
            user.id,
            AdminDebtCreateIn(
                vehicle_id=vehicle.id,
                entry_point="А-107",
                exit_point="М-7",
                amount=145,
            ),
        )
        notification = _scenario_push(
            user.id,
            enabled=payload.send_push,
            title="Есть неоплаченные поездки",
            body="Погасите задолженность, чтобы избежать штрафа.",
            deep_link="driverassistant://debts",
            type="debt_warning",
        )
    elif scenario == "heavy_commuter":
        _set_balance(user.id, 5000)
        for day in range(10):
            _create_trip(
                user.id,
                AdminTripCreateIn(
                    vehicle_id=vehicle.id,
                    started_at=datetime.now(UTC) - timedelta(days=day),
                    amount=210 + day % 3 * 30,
                ),
            )
        notification = _scenario_push(
            user.id,
            enabled=payload.send_push,
            title="Прогноз расходов обновлен",
            body="Мы пересчитали регулярный маршрут и прогноз на месяц.",
            deep_link="driverassistant://dashboard",
            type="monthly_spend_forecast",
        )
    else:
        _set_balance(user.id, 2500)
        saturday = _next_weekday(5)
        for week in range(4):
            _create_trip(
                user.id,
                AdminTripCreateIn(
                    vehicle_id=vehicle.id,
                    started_at=saturday - timedelta(days=7 * week),
                    entry_point="Москва",
                    exit_point="Зеленоград",
                    amount=260,
                ),
            )
        notification = _scenario_push(
            user.id,
            enabled=payload.send_push,
            title="Выгодное время для поездки",
            body="На выходных маршрут можно пройти дешевле после 10:20.",
            deep_link="driverassistant://recommendations",
            type="recommendation_available",
        )

    ml_result = ml_service.recalculate_user(user.id)
    return {
        "status": "completed",
        "scenario": scenario,
        "user_id": user.id,
        "phone": user.phone,
        "ml": ml_result,
        "notification": notification,
        "dashboard": get_dashboard(user.id),
    }


@router.post("/ml/recalculate-all")
async def recalculate_all() -> dict[str, object]:
    return ml_service.recalculate_all()


@router.get("/ml/status")
async def ml_status() -> dict[str, object]:
    return ml_service.get_ml_status()


@router.post("/seed")
async def seed_demo_data() -> dict[str, object]:
    notification_service.reset()
    recommendation_service.reset()
    with SessionLocal() as db:
        user = seed_db_demo_data(db)
    return {
        "status": "seeded",
        "demo_user_id": user.id,
        "demo_phone": user.phone,
    }


@router.post("/notifications/tick")
async def notification_tick() -> dict[str, object]:
    return run_notification_tick()


@router.post("/notifications/send")
async def send_notification(payload: AdminNotificationSendIn) -> dict[str, object]:
    user_ids = _resolve_notification_targets(payload)
    if not user_ids:
        raise HTTPException(status_code=404, detail="Notification target not found")

    results = [
        notification_service.dispatch_notification(
            user_id=user_id,
            type=payload.type,
            title=payload.title,
            body=payload.body,
            deep_link=payload.deep_link,
            metadata=payload.metadata,
            ignore_quiet_hours=payload.ignore_quiet_hours,
        )
        for user_id in user_ids
    ]
    return {
        "status": "completed",
        "target_count": len(user_ids),
        "created": sum(1 for result in results if result["notification"] is not None),
        "results": results,
    }


def _resolve_notification_targets(payload: AdminNotificationSendIn) -> list[str]:
    with SessionLocal() as db:
        if payload.broadcast:
            return list(db.scalars(select(UserORM.id)).all())
        if payload.user_id:
            user = db.get(UserORM, payload.user_id)
            return [user.id] if user else []
        if payload.phone:
            user = db.scalar(select(UserORM).where(UserORM.phone == payload.phone))
            return [user.id] if user else []
    raise HTTPException(
        status_code=400,
        detail="Set user_id, phone, or broadcast=true",
    )


def _admin_user_summary(user: UserORM) -> dict[str, object]:
    return {
        "id": user.id,
        "phone": user.phone,
        "segment": user.segment,
        "ml_cluster_id": user.ml_cluster_id,
        "ml_cluster_name": user.ml_cluster_name,
        "predicted_spend_next_month": user.predicted_spend_next_month,
        "favorite_route_name": user.favorite_route_name,
        "ml_updated_at": user.ml_updated_at.isoformat() if user.ml_updated_at else None,
        "balance": billing_service.get_balance(user.id),
        "debts_summary": billing_service.get_debt_summary(user.id),
    }


def _get_or_create_user(phone: str) -> UserORM:
    normalized_phone = phone.strip()
    with SessionLocal() as db:
        user = db.scalar(select(UserORM).where(UserORM.phone == normalized_phone))
        if user is None:
            user = UserORM(phone=normalized_phone)
            db.add(user)
            db.commit()
            db.refresh(user)
        db.expunge(user)
        return user


def _ensure_user_exists(user_id: str) -> None:
    with SessionLocal() as db:
        if db.get(UserORM, user_id) is None:
            raise HTTPException(status_code=404, detail="User not found")


def _ensure_primary_vehicle(
    user_id: str,
    *,
    plate_number: str = "А123ВС777",
    vehicle_name: str = "Kia Rio",
) -> VehicleORM:
    with SessionLocal() as db:
        vehicle = db.scalar(
            select(VehicleORM).where(
                VehicleORM.user_id == user_id,
                VehicleORM.is_primary.is_(True),
            )
        )
    if vehicle is None:
        created = vehicle_service.create_for_user(
            user_id,
            VehicleCreateIn(
                plate_number=plate_number,
                name=vehicle_name,
                is_primary=True,
            ),
        )
        with SessionLocal() as db:
            vehicle = db.get(VehicleORM, created.id)
            db.expunge(vehicle)
            return vehicle
    return vehicle


def _create_trip(user_id: str, payload: AdminTripCreateIn) -> dict[str, object]:
    vehicle_id = payload.vehicle_id or _ensure_primary_vehicle(user_id).id
    started_at = payload.started_at or datetime.now(UTC)
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)
    finished_at = started_at + timedelta(minutes=28)
    with SessionLocal() as db:
        vehicle = db.get(VehicleORM, vehicle_id)
        if vehicle is None or vehicle.user_id != user_id:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        trip = TripORM(
            user_id=user_id,
            vehicle_id=vehicle_id,
            road_name=payload.road_name,
            started_at=started_at,
            finished_at=finished_at,
            entry_point=payload.entry_point,
            exit_point=payload.exit_point,
            distance_km=payload.distance_km,
            amount=payload.amount,
            status=payload.status,
        )
        transaction = TransactionORM(
            user_id=user_id,
            type="debt" if payload.status == "debt" else "trip_charge",
            amount=-payload.amount,
            description=f"{payload.entry_point} -> {payload.exit_point}",
        )
        db.add_all([trip, transaction])
        db.commit()
        db.refresh(trip)
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


def _set_balance(user_id: str, target_amount: float) -> None:
    current_amount = float(billing_service.get_balance(user_id)["amount"])
    delta = round(target_amount - current_amount, 2)
    if delta == 0:
        return
    with SessionLocal() as db:
        transaction = TransactionORM(
            user_id=user_id,
            type="top_up" if delta > 0 else "trip_charge",
            amount=delta,
            description=f"Admin balance adjustment to {target_amount:.2f}",
        )
        db.add(transaction)
        db.commit()


def _scenario_push(
    user_id: str,
    *,
    enabled: bool,
    title: str,
    body: str,
    deep_link: str,
    type: str,
) -> dict[str, object] | None:
    if not enabled:
        return None
    return notification_service.dispatch_notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        deep_link=deep_link,
        metadata={"scenario": type},
        ignore_quiet_hours=True,
    )


def _reset_user_notifications(user_id: str) -> None:
    with SessionLocal() as db:
        db.query(NotificationORM).filter(NotificationORM.user_id == user_id).delete()
        db.query(RecommendationORM).filter(RecommendationORM.user_id == user_id).delete()
        db.commit()


def _next_weekday(weekday: int) -> datetime:
    now = datetime.now(UTC)
    days_ahead = (weekday - now.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return now + timedelta(days=days_ahead)
