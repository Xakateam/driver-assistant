from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.models import (
    NotificationORM,
    RecommendationORM,
    TransactionORM,
    TripORM,
    UserORM,
    VehicleORM,
    AutopaySettingORM,
)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)


def seed_demo_data(db: Session) -> UserORM:
    user = db.scalar(select(UserORM).where(UserORM.phone == "+79990000000"))
    if user is None:
        user = UserORM(phone="+79990000000", segment="commuter")
        db.add(user)
        db.flush()

    vehicle = db.scalar(select(VehicleORM).where(VehicleORM.user_id == user.id))
    if vehicle is None:
        vehicle = VehicleORM(
            user_id=user.id,
            plate_number="А123ВС777",
            name="Kia Rio",
            is_primary=True,
        )
        db.add(vehicle)
        db.flush()

    _seed_trips(db, user.id, vehicle.id)
    _seed_autopay(db, user.id)
    _seed_notifications(db, user.id)
    _seed_recommendations(db, user.id)

    db.commit()
    db.refresh(user)
    return user


def _seed_trips(db: Session, user_id: str, vehicle_id: str) -> None:
    has_trips = db.scalar(select(TripORM.id).where(TripORM.user_id == user_id).limit(1))
    if has_trips:
        return

    db.add(
        TransactionORM(
            user_id=user_id,
            type="top_up",
            amount=3000,
            description="Demo top-up",
        )
    )

    now = datetime.now(UTC)
    routes = [
        ("Ногинск", "Орехово-Зуево"),
        ("Орехово-Зуево", "Ногинск"),
        ("А-107", "М-7"),
    ]
    for day in range(1, 15):
        entry_point, exit_point = routes[day % len(routes)]
        amount = 120 + (day % 4) * 35
        started_at = now - timedelta(days=day, hours=day % 5)
        status = "debt" if day in {2, 5} else "paid"
        db.add(
            TripORM(
                user_id=user_id,
                vehicle_id=vehicle_id,
                road_name="M-12" if day % 3 else "ЦКАД",
                started_at=started_at,
                finished_at=started_at + timedelta(minutes=24 + day % 10),
                entry_point=entry_point,
                exit_point=exit_point,
                distance_km=12.5 + day % 7,
                amount=float(amount),
                status=status,
            )
        )
        db.add(
            TransactionORM(
                user_id=user_id,
                type="debt" if status == "debt" else "trip_charge",
                amount=-float(amount),
                description=f"{entry_point} -> {exit_point}",
            )
        )


def _seed_autopay(db: Session, user_id: str) -> None:
    autopay = db.get(AutopaySettingORM, user_id)
    if autopay is not None:
        return
    db.add(
        AutopaySettingORM(
            user_id=user_id,
            enabled=True,
            threshold_amount=500,
            top_up_amount=3000,
            payment_method="demo_card",
        )
    )


def _seed_notifications(db: Session, user_id: str) -> None:
    has_notifications = db.scalar(
        select(NotificationORM.id).where(NotificationORM.user_id == user_id).limit(1)
    )
    if has_notifications:
        return

    db.add_all(
        [
            NotificationORM(
                id="demo-low-balance",
                user_id=user_id,
                type="low_balance_forecast",
                title="Баланс скоро закончится",
                body="При текущем темпе поездок средств хватит примерно на 4 дня.",
                deep_link="driverassistant://topup?amount=1000",
                metadata_json={"forecast_days_left": 4, "suggested_topup": 1000},
            ),
            NotificationORM(
                id="demo-recommendation",
                user_id=user_id,
                type="recommendation_available",
                title="Есть способ сократить расходы",
                body="Посмотрите рекомендацию по более выгодному времени поездок.",
                deep_link="driverassistant://recommendations/demo-offpeak",
                metadata_json={"recommendation_id": "demo-offpeak"},
            ),
        ]
    )


def _seed_recommendations(db: Session, user_id: str) -> None:
    has_recommendations = db.scalar(
        select(RecommendationORM.id).where(RecommendationORM.user_id == user_id).limit(1)
    )
    if has_recommendations:
        return

    db.add_all(
        [
            RecommendationORM(
                id="demo-offpeak",
                user_id=user_id,
                type="offpeak_departure",
                title="Сдвиньте выезд на 20 минут",
                body=(
                    "Поездка после 10:20 обычно дешевле и снижает риск "
                    "пополнения баланса в дороге."
                ),
                priority=1,
                metadata_json={"estimated_saving_percent": 12, "suggested_time": "10:20"},
            ),
            RecommendationORM(
                id="demo-topup",
                user_id=user_id,
                type="balance_topup",
                title="Пополните баланс заранее",
                body=(
                    "Рекомендуем пополнить баланс на 1000 ₽ "
                    "до следующей регулярной поездки."
                ),
                priority=2,
                metadata_json={"amount": 1000, "currency": "RUB"},
            ),
        ]
    )
