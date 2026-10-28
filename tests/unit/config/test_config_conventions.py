"""The `.env` contract, enforced.

Every setting must be reachable as `<ENV_PREFIX>_<FIELD>`. These tests fail the
moment someone reintroduces an unprefixed name or a per-field alias — which is
how a layout ends up with an unprefixed `MIN_LEVEL` next to
`TELEMETRY_POLL_INTERVAL`.
"""

import pytest

from src.app.shared_kernel.config.app_config import AppConfig
from src.app.shared_kernel.config.base_pydantic_config import BasePydanticConfig
from src.app.shared_kernel.config.infra_configs import (
    DaemonConfig,
    DatabaseConfig,
    RedisConfig,
    TelegramConfig,
    TelemetryConfig,
)

pytestmark = [pytest.mark.unit, pytest.mark.shared_kernel]

CONFIGS = [
    (AppConfig, "APP_"),
    (DaemonConfig, "DAEMON_"),
    (DatabaseConfig, "POSTGRES_"),
    (RedisConfig, "REDIS_"),
    (TelemetryConfig, "TELEMETRY_"),
    (TelegramConfig, "TELEGRAM_"),
]


@pytest.mark.parametrize("config_cls,prefix", CONFIGS, ids=lambda v: getattr(v, "__name__", v))
class TestConfigConventions:
    def test_declares_the_expected_prefix(self, config_cls, prefix):
        assert config_cls.model_config.get("env_prefix") == prefix

    def test_no_field_uses_an_alias(self, config_cls, prefix):
        """An alias silently opts a field out of the prefix scheme."""
        aliased = [
            name
            for name, info in config_cls.model_fields.items()
            if info.alias is not None or info.validation_alias is not None
        ]
        assert aliased == []

    def test_inherits_the_shared_settings_behaviour(self, config_cls, prefix):
        # Subclasses declare only `env_prefix`; everything else is merged in from
        # BasePydanticConfig across the MRO.
        assert issubclass(config_cls, BasePydanticConfig)
        assert config_cls.model_config["env_file"] == ".env"
        assert config_cls.model_config["env_ignore_empty"] is True
        assert config_cls.model_config["extra"] == "ignore"


class TestAppConfigSurface:
    def test_exposes_only_real_settings(self):
        """Structural layout must not leak into the environment.

        `APP_ROOT` is a ClassVar; as a field it would mint an `APP_APP_ROOT`
        variable nothing is meant to set.
        """
        assert set(AppConfig.model_fields) == {
            "environment",
            "secret_key",
            "timezone",
            "aes_key",
        }

    def test_container_directory_variable_is_ignored(self, monkeypatch):
        """`APP_DIR` is the container's working directory, set in the Dockerfile.

        It shares the `APP_` namespace, so the config must ignore it rather than
        fail on an unknown field.
        """
        monkeypatch.setenv("APP_DIR", "/app")
        # Required settings, so the test does not depend on a local `.env`.
        monkeypatch.setenv("APP_SECRET_KEY", "x")
        monkeypatch.setenv("APP_AES_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")

        assert AppConfig().environment == "development"


class TestAppConfigDerivations:
    def _config(self, **overrides) -> AppConfig:
        defaults = dict(environment="development", secret_key="x", aes_key=b"0" * 32)
        defaults.update(overrides)
        return AppConfig(**defaults)

    def test_debug_follows_the_environment(self):
        assert self._config(environment="development").debug is True
        assert self._config(environment="testing").debug is True
        assert self._config(environment="production").debug is False
