import sys
import types

from app.core.config import Settings
from app.main import init_sentry


def test_sentry_settings_defaults_to_disabled(monkeypatch) -> None:
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("SENTRY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("SENTRY_TRACES_SAMPLE_RATE", raising=False)

    test_settings = Settings()

    assert test_settings.SENTRY_DSN is None
    assert test_settings.SENTRY_ENVIRONMENT == "local"
    assert test_settings.SENTRY_TRACES_SAMPLE_RATE == 0.0


def test_init_sentry_uses_fastapi_integrations(monkeypatch) -> None:
    init_calls = []

    class FastApiIntegration:
        pass

    class StarletteIntegration:
        pass

    sentry_sdk = types.ModuleType("sentry_sdk")
    sentry_sdk.init = lambda **kwargs: init_calls.append(kwargs)

    fastapi_module = types.ModuleType("sentry_sdk.integrations.fastapi")
    fastapi_module.FastApiIntegration = FastApiIntegration
    starlette_module = types.ModuleType("sentry_sdk.integrations.starlette")
    starlette_module.StarletteIntegration = StarletteIntegration

    monkeypatch.setitem(sys.modules, "sentry_sdk", sentry_sdk)
    monkeypatch.setitem(sys.modules, "sentry_sdk.integrations.fastapi", fastapi_module)
    monkeypatch.setitem(
        sys.modules,
        "sentry_sdk.integrations.starlette",
        starlette_module,
    )
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.com/1")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "test")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.25")

    init_sentry(Settings())

    assert len(init_calls) == 1
    assert init_calls[0]["dsn"] == "https://public@example.com/1"
    assert init_calls[0]["environment"] == "test"
    assert init_calls[0]["traces_sample_rate"] == 0.25
    assert isinstance(init_calls[0]["integrations"][0], StarletteIntegration)
    assert isinstance(init_calls[0]["integrations"][1], FastApiIntegration)
