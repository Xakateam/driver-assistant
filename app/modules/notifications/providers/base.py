from typing import Protocol


class PushProvider(Protocol):
    def send(
        self,
        *,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, object]:
        ...
