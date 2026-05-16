import json
from typing import Any

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from app.core.config import settings


FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


class FcmPushProvider:
    def __init__(self) -> None:
        self._credentials = None
        self._project_id: str | None = None

    def send(
        self,
        *,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, object]:
        try:
            credentials = self._load_credentials()
        except Exception as exc:
            return self._skipped(
                token=token,
                title=title,
                body=body,
                data=data,
                reason=f"FCM credentials are invalid: {exc}",
            )
        project_id = self._project_id
        if credentials is None or project_id is None:
            return self._skipped(
                token=token,
                title=title,
                body=body,
                data=data,
                reason="FCM service account is not configured",
            )

        if not credentials.valid:
            credentials.refresh(Request())

        url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json={
                "message": {
                    "token": token,
                    "notification": {"title": title, "body": body},
                    "data": data or {},
                    "android": {"priority": "HIGH"},
                }
            },
            timeout=10,
        )
        if response.ok:
            return {
                "status": "sent",
                "provider": "fcm",
                "token": token,
                "message_id": response.json().get("name"),
            }
        return {
            "status": "failed",
            "provider": "fcm",
            "token": token,
            "status_code": response.status_code,
            "response": response.text,
        }

    def is_configured(self) -> bool:
        try:
            return self._load_credentials() is not None and self._project_id is not None
        except Exception:
            return False

    def _load_credentials(self):
        if self._credentials is not None:
            return self._credentials

        credentials_info = _load_service_account_info()
        if credentials_info is None:
            return None

        self._project_id = settings.FIREBASE_PROJECT_ID or credentials_info.get(
            "project_id"
        )
        self._credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=[FCM_SCOPE],
        )
        return self._credentials

    @staticmethod
    def _skipped(
        *,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None,
        reason: str,
    ) -> dict[str, object]:
        return {
            "status": "skipped",
            "provider": "fcm",
            "reason": reason,
            "token": token,
            "title": title,
            "body": body,
            "data": data or {},
        }


def _load_service_account_info() -> dict[str, Any] | None:
    if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        return json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
    if settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        with open(settings.FIREBASE_SERVICE_ACCOUNT_PATH, encoding="utf-8") as file:
            return json.load(file)
    return None
