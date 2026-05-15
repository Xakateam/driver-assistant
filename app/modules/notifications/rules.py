from app.modules.forecasting.service import get_monthly_forecast
from app.modules.notifications.service import notification_service


def evaluate_notification_rules(user_id: str) -> list[dict[str, object]]:
    forecast = get_monthly_forecast(user_id)
    created: list[dict[str, object]] = []

    if forecast["low_balance_risk"]:
        created.append(
            notification_service.create_notification(
                user_id=user_id,
                type="low_balance_forecast",
                title="Баланс скоро закончится",
                body="Прогноз показывает риск нехватки средств до конца месяца.",
                deep_link="driverassistant://topup?amount=1000",
                metadata={"forecast": forecast},
            )
        )

    return created
