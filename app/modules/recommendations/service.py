from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import RLock


@dataclass
class Recommendation:
    id: str
    user_id: str
    type: str
    title: str
    body: str
    status: str
    priority: int
    created_at: str
    decided_at: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RecommendationService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._recommendations_by_user: dict[str, dict[str, Recommendation]] = {}

    def list_recommendations(self, *, user_id: str) -> list[dict[str, object]]:
        with self._lock:
            self._ensure_seed_recommendations(user_id)
            recommendations = self._recommendations_by_user[user_id].values()
            return [
                asdict(recommendation)
                for recommendation in sorted(
                    recommendations,
                    key=lambda item: (item.status != "pending", item.priority),
                )
            ]

    def accept(self, *, user_id: str, recommendation_id: str) -> dict[str, object] | None:
        return self._set_status(
            user_id=user_id,
            recommendation_id=recommendation_id,
            status="accepted",
        )

    def decline(self, *, user_id: str, recommendation_id: str) -> dict[str, object] | None:
        return self._set_status(
            user_id=user_id,
            recommendation_id=recommendation_id,
            status="declined",
        )

    def reset(self) -> None:
        with self._lock:
            self._recommendations_by_user.clear()

    def _set_status(
        self,
        *,
        user_id: str,
        recommendation_id: str,
        status: str,
    ) -> dict[str, object] | None:
        with self._lock:
            self._ensure_seed_recommendations(user_id)
            recommendation = self._recommendations_by_user[user_id].get(
                recommendation_id,
            )
            if recommendation is None:
                return None
            recommendation.status = status
            recommendation.decided_at = _now()
            return asdict(recommendation)

    def _ensure_seed_recommendations(self, user_id: str) -> None:
        if user_id in self._recommendations_by_user:
            return

        self._recommendations_by_user[user_id] = {
            "demo-offpeak": Recommendation(
                id="demo-offpeak",
                user_id=user_id,
                type="offpeak_departure",
                title="Сдвиньте выезд на 20 минут",
                body=(
                    "Поездка после 10:20 обычно дешевле и снижает риск "
                    "пополнения баланса в дороге."
                ),
                status="pending",
                priority=1,
                created_at=_now(),
                metadata={"estimated_saving_percent": 12, "suggested_time": "10:20"},
            ),
            "demo-topup": Recommendation(
                id="demo-topup",
                user_id=user_id,
                type="balance_topup",
                title="Пополните баланс заранее",
                body=(
                    "Рекомендуем пополнить баланс на 1000 ₽ "
                    "до следующей регулярной поездки."
                ),
                status="pending",
                priority=2,
                created_at=_now(),
                metadata={"amount": 1000, "currency": "RUB"},
            ),
        }


recommendation_service = RecommendationService()
