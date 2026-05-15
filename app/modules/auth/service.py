from dataclasses import dataclass
from threading import RLock

from app.modules.auth.jwt import create_demo_token
from app.modules.auth.otp import DEMO_OTP_CODE
from app.modules.users.service import User, user_service


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._codes_by_phone: dict[str, str] = {}
        self._access_tokens: dict[str, str] = {}
        self._refresh_tokens: dict[str, str] = {}

    def request_code(self, phone: str) -> str:
        normalized_phone = phone.strip()
        with self._lock:
            self._codes_by_phone[normalized_phone] = DEMO_OTP_CODE
        return DEMO_OTP_CODE

    def verify_code(self, phone: str, code: str) -> TokenPair | None:
        normalized_phone = phone.strip()
        with self._lock:
            expected_code = self._codes_by_phone.get(normalized_phone, DEMO_OTP_CODE)

        if code != expected_code:
            return None

        user = user_service.get_or_create_by_phone(normalized_phone)
        return self._issue_token_pair(user.id)

    def get_user_for_access_token(self, access_token: str) -> User | None:
        with self._lock:
            user_id = self._access_tokens.get(access_token)
        if user_id is None:
            return None
        return user_service.get_by_id(user_id)

    def refresh_access_token(self, refresh_token: str) -> str | None:
        with self._lock:
            user_id = self._refresh_tokens.get(refresh_token)
            if user_id is None:
                return None

            access_token = self._new_token()
            self._access_tokens[access_token] = user_id
            return access_token

    def revoke_access_token(self, access_token: str) -> None:
        with self._lock:
            self._access_tokens.pop(access_token, None)

    def _issue_token_pair(self, user_id: str) -> TokenPair:
        with self._lock:
            access_token = self._new_token()
            refresh_token = self._new_token()
            self._access_tokens[access_token] = user_id
            self._refresh_tokens[refresh_token] = user_id
            return TokenPair(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def _new_token() -> str:
        return create_demo_token()


auth_service = AuthService()
