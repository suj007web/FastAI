"""Typed runtime settings for FastAI application bootstrap."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from os import getenv

PROFILE_DEFAULTS: dict[str, dict[str, str | int]] = {
    "dev": {
        "env": "development",
        "host": "0.0.0.0",
        "port": 8000,
        "log_level": "DEBUG",
    },
    "balanced": {
        "env": "development",
        "host": "0.0.0.0",
        "port": 8000,
        "log_level": "INFO",
    },
    "quality": {
        "env": "development",
        "host": "0.0.0.0",
        "port": 8000,
        "log_level": "INFO",
    },
    "latency": {
        "env": "development",
        "host": "0.0.0.0",
        "port": 8000,
        "log_level": "WARNING",
    },
}


@dataclass(frozen=True)
class AppSettings:
    """Runtime settings loaded from environment variables."""

    profile: str = "balanced"
    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    overridden_keys: tuple[str, ...] = ()

    @classmethod
    def _resolve_profile(cls) -> str:
        """Resolve and normalize the selected config profile."""
        selected = getenv("FASTAI_CONFIG_PROFILE", cls.profile).strip().lower()
        return selected if selected in PROFILE_DEFAULTS else cls.profile

    @classmethod
    def from_env(cls) -> AppSettings:
        """Load app settings using env > profile defaults > built-in defaults."""
        profile = cls._resolve_profile()
        profile_defaults = PROFILE_DEFAULTS[profile]

        env = getenv("FASTAI_ENV")
        host = getenv("FASTAI_HOST")
        port = getenv("FASTAI_PORT")
        log_level = getenv("FASTAI_LOG_LEVEL")

        overridden_keys: list[str] = []
        if env is not None:
            overridden_keys.append("env")
        if host is not None:
            overridden_keys.append("host")
        if port is not None:
            overridden_keys.append("port")
        if log_level is not None:
            overridden_keys.append("log_level")

        return cls(
            profile=profile,
            env=env or str(profile_defaults["env"]),
            host=host or str(profile_defaults["host"]),
            port=int(port) if port is not None else int(profile_defaults["port"]),
            log_level=log_level or str(profile_defaults["log_level"]),
            overridden_keys=tuple(overridden_keys),
        )

    def summary(self) -> dict[str, object]:
        """Return startup settings summary with effective values and env overrides."""
        effective = asdict(self)
        effective.pop("overridden_keys", None)
        return {
            "effective": effective,
            "overridden_keys": list(self.overridden_keys),
        }
