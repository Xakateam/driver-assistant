from dataclasses import dataclass
from threading import RLock

from app.core.store import store


@dataclass(frozen=True)
class User:
    id: str
    phone: str
    segment: str = "commuter"


class UserService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._users_by_id: dict[str, User] = {}
        self._user_ids_by_phone: dict[str, str] = {}

    def get_or_create_by_phone(self, phone: str) -> User:
        normalized_phone = phone.strip()
        with self._lock:
            user_id = self._user_ids_by_phone.get(normalized_phone)
            if user_id is not None:
                return self._users_by_id[user_id]

            store_user = store.create_or_get_user(normalized_phone)
            user = User(
                id=store_user.id,
                phone=store_user.phone,
                segment=store_user.segment,
            )
            self._users_by_id[user.id] = user
            self._user_ids_by_phone[user.phone] = user.id
            return user

    def get_by_id(self, user_id: str) -> User | None:
        with self._lock:
            return self._users_by_id.get(user_id)


user_service = UserService()
