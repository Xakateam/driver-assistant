from app.core.store import store
from app.modules.notifications.rules import evaluate_notification_rules


def run_notification_tick() -> dict[str, object]:
    created: list[dict[str, object]] = []
    for user_id in list(store.users):
        created.extend(evaluate_notification_rules(user_id))
    return {"status": "completed", "created": len(created)}
