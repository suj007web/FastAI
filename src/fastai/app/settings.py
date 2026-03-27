"""Typed runtime settings for FastAI application bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class AppSettings:
    """Runtime settings loaded from environment variables."""

    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> AppSettings:
        """Load app settings from environment variables with defaults."""
        return cls(
            env=getenv("FASTAI_ENV", cls.env),
            host=getenv("FASTAI_HOST", cls.host),
            port=int(getenv("FASTAI_PORT", str(cls.port))),
            log_level=getenv("FASTAI_LOG_LEVEL", cls.log_level),
        )
