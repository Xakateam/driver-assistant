from app.modules.billing.service import get_balance
from app.modules.billing.service import get_autopay, get_debt_summary
from app.modules.forecasting.service import get_monthly_forecast
from app.modules.notifications.service import notification_service
from app.modules.recommendations.service import recommendation_service
from app.modules.trips.service import list_trips
from app.modules.users.service import user_service
from app.modules.vehicles.service import vehicle_service


def get_dashboard(user_id: str) -> dict[str, object]:
    user = user_service.get_by_id(user_id) or user_service.get_or_create_by_phone(
        "+79990000000"
    )
    return {
        "user": {
            "id": user.id,
            "phone": user.phone,
            "segment": user.segment,
        },
        "balance": get_balance(user.id),
        "autopay": get_autopay(user.id),
        "forecast": get_monthly_forecast(user.id),
        "debts_summary": get_debt_summary(user.id),
        "primary_vehicle": _primary_vehicle(user.id),
        "recent_trips": list_trips(user.id, None, None, None)[:3],
        "notifications": notification_service.list_notifications(user_id=user.id)[:3],
        "recommendations": recommendation_service.list_recommendations(user_id=user.id)[:3],
    }


def _primary_vehicle(user_id: str) -> dict[str, object] | None:
    vehicles = vehicle_service.list_for_user(user_id)
    primary = next((vehicle for vehicle in vehicles if vehicle.is_primary), None)
    if primary is None and vehicles:
        primary = vehicles[0]
    if primary is None:
        return None
    return {
        "id": primary.id,
        "plate_number": primary.plate_number,
        "name": primary.name,
        "is_primary": primary.is_primary,
    }
