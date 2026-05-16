from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import CurrentUserDep
from app.api.v1.schemas import (
    DeviceRegisterOut,
    NotificationActionOut,
    NotificationOut,
    NotificationRuleOut,
)
from app.modules.notifications.service import notification_service

router = APIRouter()


class DeviceRegisterIn(BaseModel):
    platform: str = Field(default="android")
    fcm_token: str


class NotificationActionIn(BaseModel):
    action: str = Field(examples=["accepted"])


class NotificationRuleUpdateIn(BaseModel):
    enabled: bool


@router.post("/devices/register", response_model=DeviceRegisterOut)
async def register_device(
    payload: DeviceRegisterIn,
    current_user: CurrentUserDep,
) -> DeviceRegisterOut:
    return notification_service.register_device(
        user_id=current_user.id,
        platform=payload.platform,
        fcm_token=payload.fcm_token,
    )


@router.get("", response_model=list[NotificationOut])
async def get_notifications(current_user: CurrentUserDep) -> list[NotificationOut]:
    return notification_service.list_notifications(user_id=current_user.id)


@router.get("/rules", response_model=list[NotificationRuleOut])
async def get_notification_rules() -> list[NotificationRuleOut]:
    return notification_service.list_rules()


@router.patch("/rules/{rule_id}", response_model=NotificationRuleOut)
async def update_notification_rule(
    rule_id: str,
    payload: NotificationRuleUpdateIn,
) -> NotificationRuleOut:
    rule = notification_service.update_rule(rule_id=rule_id, enabled=payload.enabled)
    if rule is None:
        raise HTTPException(status_code=404, detail="Notification rule not found")
    return rule


@router.get("/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: str,
    current_user: CurrentUserDep,
) -> NotificationOut:
    notification = notification_service.get_notification(
        user_id=current_user.id,
        notification_id=notification_id,
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_as_read(
    notification_id: str,
    current_user: CurrentUserDep,
) -> NotificationOut:
    notification = notification_service.mark_as_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/{notification_id}/action", response_model=NotificationActionOut)
async def handle_action(
    notification_id: str,
    payload: NotificationActionIn,
    current_user: CurrentUserDep,
) -> NotificationActionOut:
    result = notification_service.save_action(
        user_id=current_user.id,
        notification_id=notification_id,
        action=payload.action,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return result
