from app.core.store import store
from app.modules.billing.service import get_balance
from app.modules.forecasting.service import get_monthly_forecast
from app.modules.notifications.service import notification_service
from app.modules.recommendations.service import recommendation_service


def get_dashboard(user_id: str) -> dict[str, object]:
    user = store.get_user(user_id) or store.seed_demo_data()
    return {
        "user": {
            "id": user.id,
            "phone": user.phone,
            "segment": user.segment,
        },
        "balance": get_balance(user.id),
        "forecast": get_monthly_forecast(user.id),
        "notifications": notification_service.list_notifications(user_id=user.id)[:3],
        "recommendations": recommendation_service.list_recommendations(user_id=user.id)[:3],
    }
