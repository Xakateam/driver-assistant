from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import CurrentUserDep
from app.modules.notifications.service import notification_service

router = APIRouter()


class DeviceRegisterIn(BaseModel):
    platform: str = Field(default="android")
    fcm_token: str


class NotificationActionIn(BaseModel):
    action: str = Field(examples=["accepted"])


class NotificationRuleUpdateIn(BaseModel):
    enabled: bool


@router.post("/devices/register")
async def register_device(
    payload: DeviceRegisterIn,
    current_user: CurrentUserDep,
) -> dict[str, object]:
    return notification_service.register_device(
        user_id=current_user.id,
        platform=payload.platform,
        fcm_token=payload.fcm_token,
    )


@router.get("")
async def get_notifications(current_user: CurrentUserDep) -> list[dict[str, object]]:
    return notification_service.list_notifications(user_id=current_user.id)


@router.get("/rules")
async def get_notification_rules() -> list[dict[str, object]]:
    return notification_service.list_rules()


@router.patch("/rules/{rule_id}")
async def update_notification_rule(
    rule_id: str,
    payload: NotificationRuleUpdateIn,
) -> dict[str, object]:
    rule = notification_service.update_rule(rule_id=rule_id, enabled=payload.enabled)
    if rule is None:
        raise HTTPException(status_code=404, detail="Notification rule not found")
    return rule


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    current_user: CurrentUserDep,
) -> dict[str, object]:
    notification = notification_service.get_notification(
        user_id=current_user.id,
        notification_id=notification_id,
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: CurrentUserDep,
) -> dict[str, object]:
    notification = notification_service.mark_as_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/{notification_id}/action")
async def handle_action(
    notification_id: str,
    payload: NotificationActionIn,
    current_user: CurrentUserDep,
) -> dict[str, object]:
    result = notification_service.save_action(
        user_id=current_user.id,
        notification_id=notification_id,
        action=payload.action,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return result
