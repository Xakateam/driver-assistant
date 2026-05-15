class MockPushProvider:
    def send(
        self,
        *,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, object]:
        return {
            "status": "sent",
            "provider": "mock",
            "token": token,
            "title": title,
            "body": body,
            "data": data or {},
        }
