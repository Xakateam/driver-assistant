from app.modules.notifications.providers.fcm import FcmPushProvider
from app.modules.notifications.providers.mock import MockPushProvider


_fcm_provider = FcmPushProvider()
_mock_provider = MockPushProvider()


def get_push_provider():
    if _fcm_provider.is_configured():
        return _fcm_provider
    return _mock_provider
