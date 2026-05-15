class FcmPushProvider:
    def send(
        self,
        *,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, object]:
        # Placeholder adapter. Real FCM credentials and HTTP calls are wired later.
        return {
            "status": "skipped",
            "provider": "fcm",
            "reason": "FCM credentials are not configured",
            "token": token,
            "title": title,
            "body": body,
            "data": data or {},
        }
