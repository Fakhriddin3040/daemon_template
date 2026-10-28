import base64
from datetime import tzinfo
from functools import cached_property
from pathlib import Path
from typing import ClassVar

from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict

from src.app.shared_kernel.config.base_pydantic_config import BasePydanticConfig
from src.app.shared_kernel.constants.datetime_const import resolve_timezone
from src.app.shared_kernel.types.base_types import Environment

_DEBUG_ENVIRONMENTS = ("development", "testing")


class AppConfig(BasePydanticConfig):
    """Everything under ``APP_*``."""

    model_config = SettingsConfigDict(env_prefix="APP_")

    environment: Environment = Field(default="development")

    secret_key: str

    # IANA name, e.g. "Europe/Berlin". UTC by default — see datetime_const.
    timezone: str = Field(default="UTC")

    # AES secret, given base64-encoded and decoded to raw bytes at parse time.
    aes_key: bytes

    # The repository root. A ClassVar, not a field: nothing is meant to set it.
    APP_ROOT: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.parent

    @field_validator("aes_key", mode="before")
    def secret_key_validator(cls, v) -> bytes:
        if isinstance(v, bytes):
            return v

        return base64.b64decode(v.encode("utf-8"))

    @property
    def debug(self) -> bool:
        return self.environment in _DEBUG_ENVIRONMENTS

    @cached_property
    def tzinfo(self) -> tzinfo:
        return resolve_timezone(self.timezone)
