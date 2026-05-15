from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4


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
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class NotificationRule:
    id: str
    type: str
    title: str
    enabled: bool
    channel: str
    placeholder: bool = True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class NotificationService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._devices_by_user: dict[str, dict[str, DeviceToken]] = {}
        self._notifications_by_user: dict[str, dict[str, Notification]] = {}
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
        with self._lock:
            now = _now()
            devices = self._devices_by_user.setdefault(user_id, {})
            existing = devices.get(fcm_token)
            if existing is None:
                existing = DeviceToken(
                    id=f"device-{uuid4().hex[:12]}",
                    user_id=user_id,
                    platform=platform,
                    fcm_token=fcm_token,
                    created_at=now,
                    updated_at=now,
                )
                devices[fcm_token] = existing
            else:
                existing.platform = platform
                existing.updated_at = now

            return {
                "id": existing.id,
                "status": "registered",
                "platform": existing.platform,
                "created_at": existing.created_at,
                "updated_at": existing.updated_at,
            }

    def list_notifications(self, *, user_id: str) -> list[dict[str, object]]:
        with self._lock:
            self._ensure_seed_notifications(user_id)
            notifications = self._notifications_by_user[user_id].values()
            return [
                self._notification_to_dict(notification)
                for notification in sorted(
                    notifications,
                    key=lambda item: item.created_at,
                    reverse=True,
                )
            ]

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
        with self._lock:
            self._ensure_seed_notifications(user_id)
            notification = Notification(
                id=f"notification-{uuid4().hex[:12]}",
                user_id=user_id,
                type=type,
                title=title,
                body=body,
                deep_link=deep_link,
                status="unread",
                created_at=_now(),
                metadata=metadata or {},
            )
            self._notifications_by_user[user_id][notification.id] = notification
            return self._notification_to_dict(notification)

    def get_notification(
        self,
        *,
        user_id: str,
        notification_id: str,
    ) -> dict[str, object] | None:
        with self._lock:
            self._ensure_seed_notifications(user_id)
            notification = self._notifications_by_user[user_id].get(notification_id)
            if notification is None:
                return None
            return self._notification_to_dict(notification)

    def mark_as_read(
        self,
        *,
        user_id: str,
        notification_id: str,
    ) -> dict[str, object] | None:
        with self._lock:
            self._ensure_seed_notifications(user_id)
            notification = self._notifications_by_user[user_id].get(notification_id)
            if notification is None:
                return None
            if notification.status != "read":
                notification.status = "read"
                notification.read_at = _now()
            return self._notification_to_dict(notification)

    def save_action(
        self,
        *,
        user_id: str,
        notification_id: str,
        action: str,
    ) -> dict[str, object] | None:
        with self._lock:
            self._ensure_seed_notifications(user_id)
            notification = self._notifications_by_user[user_id].get(notification_id)
            if notification is None:
                return None
            notification.action = action
            notification.action_at = _now()
            return {
                "id": notification.id,
                "action": notification.action,
                "status": "saved",
                "action_at": notification.action_at,
            }

    def list_rules(self) -> list[dict[str, object]]:
        with self._lock:
            return [asdict(rule) for rule in self._rules.values()]

    def update_rule(self, *, rule_id: str, enabled: bool) -> dict[str, object] | None:
        with self._lock:
            rule = self._rules.get(rule_id)
            if rule is None:
                return None
            rule.enabled = enabled
            return asdict(rule)

    def reset(self) -> None:
        with self._lock:
            self._devices_by_user.clear()
            self._notifications_by_user.clear()
            self._rules = self._default_rules()

    def _ensure_seed_notifications(self, user_id: str) -> None:
        if user_id in self._notifications_by_user:
            return

        self._notifications_by_user[user_id] = {
            "demo-low-balance": Notification(
                id="demo-low-balance",
                user_id=user_id,
                type="low_balance_forecast",
                title="Баланс скоро закончится",
                body="При текущем темпе поездок средств хватит примерно на 4 дня.",
                deep_link="driverassistant://topup?amount=1000",
                status="unread",
                created_at=_now(),
                metadata={"forecast_days_left": 4, "suggested_topup": 1000},
            ),
            "demo-recommendation": Notification(
                id="demo-recommendation",
                user_id=user_id,
                type="recommendation_available",
                title="Есть способ сократить расходы",
                body="Посмотрите рекомендацию по более выгодному времени поездок.",
                deep_link="driverassistant://recommendations/demo-offpeak",
                status="unread",
                created_at=_now(),
                metadata={"recommendation_id": "demo-offpeak"},
            ),
        }

    @staticmethod
    def _notification_to_dict(notification: Notification) -> dict[str, object]:
        return asdict(notification)


notification_service = NotificationService()
