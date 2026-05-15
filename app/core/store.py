from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import Lock
from uuid import uuid4


class TransactionType(StrEnum):
    TOP_UP = "top_up"
    TRIP_CHARGE = "trip_charge"
    DEBT = "debt"


class NotificationStatus(StrEnum):
    CREATED = "created"
    SENT = "sent"
    FAILED = "failed"
    UNREAD = "unread"
    READ = "read"


class RecommendationStatus(StrEnum):
    ACTIVE = "active"
    ACCEPTED = "accepted"
    DECLINED = "declined"


@dataclass(slots=True)
class UserRecord:
    id: str
    phone: str
    segment: str = "commuter"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class VehicleRecord:
    id: str
    user_id: str
    plate_number: str
    name: str | None = None
    is_primary: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class TripRecord:
    id: str
    user_id: str
    vehicle_id: str
    started_at: datetime
    finished_at: datetime
    entry_point: str
    exit_point: str
    distance_km: float
    amount: float
    status: str = "paid"


@dataclass(slots=True)
class TransactionRecord:
    id: str
    user_id: str
    type: TransactionType
    amount: float
    description: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class NotificationRecord:
    id: str
    user_id: str
    type: str
    title: str
    body: str
    deep_link: str | None = None
    status: NotificationStatus = NotificationStatus.UNREAD
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    read_at: datetime | None = None
    action: str | None = None


@dataclass(slots=True)
class RecommendationRecord:
    id: str
    user_id: str
    type: str
    title: str
    body: str
    status: RecommendationStatus = RecommendationStatus.ACTIVE
    expected_saving: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class DeviceTokenRecord:
    id: str
    user_id: str
    platform: str
    fcm_token: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.users: dict[str, UserRecord] = {}
        self.users_by_phone: dict[str, str] = {}
        self.vehicles: dict[str, VehicleRecord] = {}
        self.trips: dict[str, TripRecord] = {}
        self.transactions: dict[str, TransactionRecord] = {}
        self.notifications: dict[str, NotificationRecord] = {}
        self.recommendations: dict[str, RecommendationRecord] = {}
        self.device_tokens: dict[str, DeviceTokenRecord] = {}
        self.seed_demo_data()

    def seed_demo_data(self) -> UserRecord:
        with self._lock:
            self.users.clear()
            self.users_by_phone.clear()
            self.vehicles.clear()
            self.trips.clear()
            self.transactions.clear()
            self.notifications.clear()
            self.recommendations.clear()
            self.device_tokens.clear()

            user = self.create_or_get_user("+79990000000", segment="commuter")
            vehicle = self.create_vehicle(
                user_id=user.id,
                plate_number="А123ВС777",
                name="Kia Rio",
                is_primary=True,
            )

            now = datetime.now(UTC)
            routes = [
                ("Адлер", "Сириус"),
                ("Сириус", "Красная Поляна"),
                ("Олимпийский парк", "Адлер"),
            ]
            for day in range(1, 15):
                entry, exit_point = routes[day % len(routes)]
                amount = 120 + (day % 4) * 35
                started_at = now - timedelta(days=day, hours=day % 5)
                self.create_trip(
                    user_id=user.id,
                    vehicle_id=vehicle.id,
                    started_at=started_at,
                    finished_at=started_at + timedelta(minutes=24 + day % 10),
                    entry_point=entry,
                    exit_point=exit_point,
                    distance_km=12.5 + day % 7,
                    amount=float(amount),
                )

            self.create_transaction(
                user_id=user.id,
                type=TransactionType.TOP_UP,
                amount=3000,
                description="Demo top-up",
            )
            self.create_notification(
                user_id=user.id,
                type="low_balance_forecast",
                title="Баланс скоро закончится",
                body="При текущем темпе поездок средств хватит примерно на 4 дня.",
                deep_link="driverassistant://topup?amount=1000",
            )
            self.create_recommendation(
                user_id=user.id,
                type="auto_topup",
                title="Пополнить баланс заранее",
                body="Рекомендуем пополнить счет на 1000 ₽, чтобы избежать задолженности.",
                expected_saving=0,
            )
            return user

    def create_or_get_user(self, phone: str, segment: str = "commuter") -> UserRecord:
        user_id = self.users_by_phone.get(phone)
        if user_id:
            return self.users[user_id]
        user = UserRecord(id=str(uuid4()), phone=phone, segment=segment)
        self.users[user.id] = user
        self.users_by_phone[user.phone] = user.id
        return user

    def get_user(self, user_id: str) -> UserRecord | None:
        return self.users.get(user_id)

    def create_vehicle(
        self,
        user_id: str,
        plate_number: str,
        name: str | None,
        is_primary: bool,
    ) -> VehicleRecord:
        if is_primary:
            for vehicle in self.vehicles.values():
                if vehicle.user_id == user_id:
                    vehicle.is_primary = False
        vehicle = VehicleRecord(
            id=str(uuid4()),
            user_id=user_id,
            plate_number=plate_number,
            name=name,
            is_primary=is_primary,
        )
        self.vehicles[vehicle.id] = vehicle
        return vehicle

    def list_vehicles(self, user_id: str) -> list[VehicleRecord]:
        return [vehicle for vehicle in self.vehicles.values() if vehicle.user_id == user_id]

    def create_trip(
        self,
        user_id: str,
        vehicle_id: str,
        started_at: datetime,
        finished_at: datetime,
        entry_point: str,
        exit_point: str,
        distance_km: float,
        amount: float,
    ) -> TripRecord:
        trip = TripRecord(
            id=str(uuid4()),
            user_id=user_id,
            vehicle_id=vehicle_id,
            started_at=started_at,
            finished_at=finished_at,
            entry_point=entry_point,
            exit_point=exit_point,
            distance_km=distance_km,
            amount=amount,
        )
        self.trips[trip.id] = trip
        self.create_transaction(
            user_id=user_id,
            type=TransactionType.TRIP_CHARGE,
            amount=-amount,
            description=f"{entry_point} -> {exit_point}",
        )
        return trip

    def list_trips(
        self,
        user_id: str,
        vehicle_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[TripRecord]:
        trips = [trip for trip in self.trips.values() if trip.user_id == user_id]
        if vehicle_id:
            trips = [trip for trip in trips if trip.vehicle_id == vehicle_id]
        if date_from:
            trips = [trip for trip in trips if trip.started_at >= date_from]
        if date_to:
            trips = [trip for trip in trips if trip.started_at <= date_to]
        return sorted(trips, key=lambda trip: trip.started_at, reverse=True)

    def create_transaction(
        self,
        user_id: str,
        type: TransactionType,
        amount: float,
        description: str,
    ) -> TransactionRecord:
        transaction = TransactionRecord(
            id=str(uuid4()),
            user_id=user_id,
            type=type,
            amount=amount,
            description=description,
        )
        self.transactions[transaction.id] = transaction
        return transaction

    def list_transactions(self, user_id: str) -> list[TransactionRecord]:
        transactions = [
            transaction
            for transaction in self.transactions.values()
            if transaction.user_id == user_id
        ]
        return sorted(transactions, key=lambda item: item.created_at, reverse=True)

    def get_balance(self, user_id: str) -> float:
        return round(sum(item.amount for item in self.list_transactions(user_id)), 2)

    def create_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        deep_link: str | None = None,
    ) -> NotificationRecord:
        notification = NotificationRecord(
            id=str(uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            deep_link=deep_link,
        )
        self.notifications[notification.id] = notification
        return notification

    def list_notifications(self, user_id: str) -> list[NotificationRecord]:
        notifications = [
            notification
            for notification in self.notifications.values()
            if notification.user_id == user_id
        ]
        return sorted(notifications, key=lambda item: item.created_at, reverse=True)

    def create_recommendation(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        expected_saving: float | None = None,
    ) -> RecommendationRecord:
        recommendation = RecommendationRecord(
            id=str(uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            expected_saving=expected_saving,
        )
        self.recommendations[recommendation.id] = recommendation
        return recommendation

    def list_recommendations(self, user_id: str) -> list[RecommendationRecord]:
        recommendations = [
            recommendation
            for recommendation in self.recommendations.values()
            if recommendation.user_id == user_id
        ]
        return sorted(recommendations, key=lambda item: item.created_at, reverse=True)


store = InMemoryStore()
