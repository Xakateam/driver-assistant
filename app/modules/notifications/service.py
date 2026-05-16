from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.db.models import DeviceTokenORM, NotificationORM
from app.modules.notifications.providers.factory import get_push_provider


@dataclass
class DeviceToken:
    id: str
    user_id: str
    platform: str
    fcm_token: str
    created_at: str
    updated_at: str


@dataclass
class Notification:
    id: str
    user_id: str
    type: str
    title: str
    body: str
    deep_link: str | None
    status: str
    created_at: str
    read_at: str | None = None
    action: str | None = None
    action_at: str | None = None
    metadata: dict[str, object] | None = None


@dataclass
class NotificationRule:
    id: str
    type: str
    title: str
    enabled: bool
    channel: str
    placeholder: bool = True


def _now() -> datetime:
    return datetime.now(UTC)


class NotificationService:
    def __init__(self) -> None:
        self._rules: dict[str, NotificationRule] = self._default_rules()

    @staticmethod
    def _default_rules() -> dict[str, NotificationRule]:
        return {
            "low_balance_forecast": NotificationRule(
                id="low_balance_forecast",
                type="low_balance_forecast",
                title="Баланс скоро закончится",
                enabled=True,
                channel="push",
            ),
            "recommendation_available": NotificationRule(
                id="recommendation_available",
                type="recommendation_available",
                title="Новая рекомендация",
                enabled=True,
                channel="push",
            ),
            "topup_success": NotificationRule(
                id="topup_success",
                type="topup_success",
                title="Пополнение баланса",
                enabled=True,
                channel="push",
            ),
            "monthly_spend_forecast": NotificationRule(
                id="monthly_spend_forecast",
                type="monthly_spend_forecast",
                title="Прогноз расходов за месяц",
                enabled=True,
                channel="push",
            ),
            "recurring_trip_reminder": NotificationRule(
                id="recurring_trip_reminder",
                type="recurring_trip_reminder",
                title="Регулярная поездка",
                enabled=True,
                channel="push",
            ),
            "debt_warning": NotificationRule(
                id="debt_warning",
                type="debt_warning",
                title="Есть задолженность",
                enabled=True,
                channel="push",
            ),
        }

    def register_device(
        self,
        *,
        user_id: str,
        platform: str,
        fcm_token: str,
    ) -> dict[str, object]:
        with SessionLocal() as db:
            existing = db.scalar(
                select(DeviceTokenORM).where(
                    DeviceTokenORM.user_id == user_id,
                    DeviceTokenORM.fcm_token == fcm_token,
                )
            )
            if existing is None:
                existing = DeviceTokenORM(
                    user_id=user_id,
                    platform=platform,
                    fcm_token=fcm_token,
                )
                db.add(existing)
            else:
                existing.platform = platform
                existing.updated_at = _now()
            db.commit()
            db.refresh(existing)
            return {
                "id": existing.id,
                "status": "registered",
                "platform": existing.platform,
                "created_at": existing.created_at.isoformat(),
                "updated_at": existing.updated_at.isoformat(),
            }

    def list_notifications(self, *, user_id: str) -> list[dict[str, object]]:
        with SessionLocal() as db:
            self._ensure_seed_notifications(db, user_id)
            notifications = db.scalars(
                select(NotificationORM)
                .where(NotificationORM.user_id == user_id)
                .order_by(NotificationORM.created_at.desc())
            ).all()
            return [self._notification_to_dict(notification) for notification in notifications]

    def create_notification(
        self,
        *,
        user_id: str,
        type: str,
        title: str,
        body: str,
        deep_link: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        with SessionLocal() as db:
            notification = NotificationORM(
                id=f"notification-{uuid4().hex[:12]}",
                user_id=user_id,
                type=type,
                title=title,
                body=body,
                deep_link=deep_link,
                status="unread",
                metadata_json=metadata or {},
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return self._notification_to_dict(notification)

    def dispatch_notification(
        self,
        *,
        user_id: str,
        type: str,
        title: str,
        body: str,
        deep_link: str | None = None,
        metadata: dict[str, object] | None = None,
        ignore_quiet_hours: bool = False,
        dedupe_window_minutes: int | None = None,
    ) -> dict[str, object]:
        if dedupe_window_minutes is not None and self.has_recent_notification(
            user_id=user_id,
            type=type,
            window_minutes=dedupe_window_minutes,
        ):
            return {
                "status": "deduplicated",
                "notification": None,
                "deliveries": [],
            }

        notification = self.create_notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            deep_link=deep_link,
            metadata=metadata,
        )
        deliveries = self.deliver_notification(
            user_id=user_id,
            notification=notification,
            ignore_quiet_hours=ignore_quiet_hours,
        )
        return {
            "status": "created",
            "notification": notification,
            "deliveries": deliveries,
        }

    def deliver_notification(
        self,
        *,
        user_id: str,
        notification: dict[str, object],
        ignore_quiet_hours: bool = False,
    ) -> list[dict[str, object]]:
        if not ignore_quiet_hours and not is_notification_window_open():
            return [
                {
                    "status": "skipped",
                    "reason": "quiet_hours",
                    "provider": "none",
                }
            ]

        with SessionLocal() as db:
            tokens = db.scalars(
                select(DeviceTokenORM).where(DeviceTokenORM.user_id == user_id)
            ).all()

        if not tokens:
            return [
                {
                    "status": "skipped",
                    "reason": "no_device_tokens",
                    "provider": "none",
                }
            ]

        provider = get_push_provider()
        data = _notification_data(notification)
        return [
            provider.send(
                token=device.fcm_token,
                title=str(notification["title"]),
                body=str(notification["body"]),
                data=data,
            )
            for device in tokens
        ]

    def has_recent_notification(
        self,
        *,
        user_id: str,
        type: str,
        window_minutes: int,
    ) -> bool:
        cutoff = _now() - timedelta(minutes=window_minutes)
        with SessionLocal() as db:
            notification_id = db.scalar(
                select(NotificationORM.id)
                .where(
                    NotificationORM.user_id == user_id,
                    NotificationORM.type == type,
                    NotificationORM.created_at >= cutoff,
                )
                .limit(1)
            )
            return notification_id is not None

    def get_notification(
        self,
        *,
        user_id: str,
        notification_id: str,
    ) -> dict[str, object] | None:
        with SessionLocal() as db:
            notification = db.get(NotificationORM, notification_id)
            if notification is None or notification.user_id != user_id:
                return None
            return self._notification_to_dict(notification)

    def mark_as_read(
        self,
        *,
        user_id: str,
        notification_id: str,
    ) -> dict[str, object] | None:
        with SessionLocal() as db:
            notification = db.get(NotificationORM, notification_id)
            if notification is None or notification.user_id != user_id:
                return None
            notification.status = "read"
            notification.read_at = _now()
            db.commit()
            db.refresh(notification)
            return self._notification_to_dict(notification)

    def save_action(
        self,
        *,
        user_id: str,
        notification_id: str,
        action: str,
    ) -> dict[str, object] | None:
        with SessionLocal() as db:
            notification = db.get(NotificationORM, notification_id)
            if notification is None or notification.user_id != user_id:
                return None
            notification.action = action
            notification.action_at = _now()
            db.commit()
            db.refresh(notification)
            return {
                "id": notification.id,
                "action": notification.action,
                "status": "saved",
                "action_at": notification.action_at.isoformat(),
            }

    def list_rules(self) -> list[dict[str, object]]:
        return [asdict(rule) for rule in self._rules.values()]

    def update_rule(self, *, rule_id: str, enabled: bool) -> dict[str, object] | None:
        rule = self._rules.get(rule_id)
        if rule is None:
            return None
        rule.enabled = enabled
        return asdict(rule)

    def is_rule_enabled(self, rule_id: str) -> bool:
        rule = self._rules.get(rule_id)
        return bool(rule and rule.enabled)

    def reset(self) -> None:
        with SessionLocal() as db:
            db.query(DeviceTokenORM).delete()
            db.query(NotificationORM).delete()
            db.commit()
        self._rules = self._default_rules()

    @staticmethod
    def _ensure_seed_notifications(db, user_id: str) -> None:
        has_notifications = db.scalar(
            select(NotificationORM.id).where(NotificationORM.user_id == user_id).limit(1)
        )
        if has_notifications:
            return
        db.add_all(
            [
                NotificationORM(
                    id=f"demo-low-balance-{user_id[:8]}",
                    user_id=user_id,
                    type="low_balance_forecast",
                    title="Баланс скоро закончится",
                    body="При текущем темпе поездок средств хватит примерно на 4 дня.",
                    deep_link="driverassistant://topup?amount=1000",
                    metadata_json={"forecast_days_left": 4, "suggested_topup": 1000},
                ),
                NotificationORM(
                    id=f"demo-recommendation-{user_id[:8]}",
                    user_id=user_id,
                    type="recommendation_available",
                    title="Есть способ сократить расходы",
                    body="Посмотрите рекомендацию по более выгодному времени поездок.",
                    deep_link="driverassistant://recommendations/demo-offpeak",
                    metadata_json={"recommendation_id": "demo-offpeak"},
                ),
            ]
        )
        db.commit()

    @staticmethod
    def _notification_to_dict(notification: NotificationORM) -> dict[str, object]:
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "type": notification.type,
            "title": notification.title,
            "body": notification.body,
            "deep_link": notification.deep_link,
            "status": notification.status,
            "created_at": notification.created_at.isoformat(),
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "action": notification.action,
            "action_at": notification.action_at.isoformat()
            if notification.action_at
            else None,
            "metadata": notification.metadata_json,
        }


notification_service = NotificationService()


def is_notification_window_open(now: datetime | None = None) -> bool:
    from zoneinfo import ZoneInfo

    current = now or datetime.now(ZoneInfo(settings.NOTIFICATION_TIMEZONE))
    if current.tzinfo is None:
        current = current.replace(tzinfo=ZoneInfo(settings.NOTIFICATION_TIMEZONE))
    local_hour = current.astimezone(ZoneInfo(settings.NOTIFICATION_TIMEZONE)).hour
    start = settings.NOTIFICATION_ALLOWED_START_HOUR
    end = settings.NOTIFICATION_ALLOWED_END_HOUR
    if start < end:
        return start <= local_hour < end
    return local_hour >= start or local_hour < end


def _notification_data(notification: dict[str, object]) -> dict[str, str]:
    metadata = notification.get("metadata") or {}
    data = {
        "notification_id": str(notification["id"]),
        "type": str(notification["type"]),
    }
    deep_link = notification.get("deep_link")
    if deep_link:
        data["deep_link"] = str(deep_link)
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                data[f"metadata_{key}"] = str(value)
    return data
