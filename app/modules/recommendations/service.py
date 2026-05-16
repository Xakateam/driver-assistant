from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.models import RecommendationORM
from app.modules.ml.recommendations import (
    get_recommendation_category,
    predict_recommendation_ctr,
)


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
    metadata: dict[str, object] | None = None


def _now() -> datetime:
    return datetime.now(UTC)


class RecommendationService:
    def list_recommendations(self, *, user_id: str) -> list[dict[str, object]]:
        with SessionLocal() as db:
            self._ensure_seed_recommendations(db, user_id)
            recommendations = db.scalars(
                select(RecommendationORM)
                .where(RecommendationORM.user_id == user_id)
                .order_by(RecommendationORM.priority, RecommendationORM.created_at.desc())
            ).all()
            items = [
                self._recommendation_to_dict(recommendation)
                for recommendation in recommendations
            ]
            return sorted(
                items,
                key=lambda item: (
                    -float(item["predicted_ctr"]),
                    int(item["priority"]),
                ),
            )

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
        with SessionLocal() as db:
            db.query(RecommendationORM).delete()
            db.commit()

    def _set_status(
        self,
        *,
        user_id: str,
        recommendation_id: str,
        status: str,
    ) -> dict[str, object] | None:
        with SessionLocal() as db:
            recommendation = db.get(RecommendationORM, recommendation_id)
            if recommendation is None or recommendation.user_id != user_id:
                return None
            recommendation.status = status
            recommendation.decided_at = _now()
            db.commit()
            db.refresh(recommendation)
            return self._recommendation_to_dict(recommendation)

    @staticmethod
    def _ensure_seed_recommendations(db, user_id: str) -> None:
        has_recommendations = db.scalar(
            select(RecommendationORM.id)
            .where(RecommendationORM.user_id == user_id)
            .limit(1)
        )
        if has_recommendations:
            return
        db.add_all(
            [
                RecommendationORM(
                    id=f"demo-offpeak-{user_id[:8]}",
                    user_id=user_id,
                    type="offpeak_departure",
                    title="Сдвиньте выезд на 20 минут",
                    body=(
                        "Поездка после 10:20 обычно дешевле и снижает риск "
                        "пополнения баланса в дороге."
                    ),
                    priority=1,
                    metadata_json={
                        "category_id": 4,
                        "estimated_saving_percent": 12,
                        "suggested_time": "10:20",
                    },
                ),
                RecommendationORM(
                    id=f"demo-topup-{user_id[:8]}",
                    user_id=user_id,
                    type="balance_topup",
                    title="Пополните баланс заранее",
                    body=(
                        "Рекомендуем пополнить баланс на 1000 ₽ "
                        "до следующей регулярной поездки."
                    ),
                    priority=2,
                    metadata_json={"category_id": 3, "amount": 1000, "currency": "RUB"},
                ),
            ]
        )
        db.commit()

    @staticmethod
    def _recommendation_to_dict(recommendation: RecommendationORM) -> dict[str, object]:
        metadata = recommendation.metadata_json or {}
        category_id = int(
            metadata.get("category_id")
            or get_recommendation_category(recommendation.type)
        )
        ctr_prediction = predict_recommendation_ctr(
            recommendation.user_id,
            category_id,
        )
        enriched_metadata = {
            **metadata,
            "category_id": category_id,
            "ctr_source": ctr_prediction["source"],
        }
        return {
            "id": recommendation.id,
            "user_id": recommendation.user_id,
            "type": recommendation.type,
            "category_id": category_id,
            "title": recommendation.title,
            "body": recommendation.body,
            "status": recommendation.status,
            "priority": recommendation.priority,
            "predicted_ctr": ctr_prediction["predicted_ctr"],
            "created_at": recommendation.created_at.isoformat(),
            "decided_at": recommendation.decided_at.isoformat()
            if recommendation.decided_at
            else None,
            "metadata": enriched_metadata,
        }


recommendation_service = RecommendationService()
