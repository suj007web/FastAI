"""Generic helper functions used during config resolution."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


def pick(*values: T | None) -> T | None:
    """Return the first non-None value from ordered candidates."""
    for value in values:
        if value is not None:
            return value
    return None


def pick_required(*values: T | None) -> T:
    """Return first non-None value or raise when all candidates are None."""
    picked = pick(*values)
    if picked is None:
        raise ValueError("Unable to resolve required configuration value.")
    return picked


def parse_bool(value: str | None) -> bool | None:
    """Parse common truthy/falsey string values."""
    if value is None:
        return None
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_int(value: str | None) -> int | None:
    """Parse integer values from environment variables."""
    if value is None:
        return None
    return int(value)


def parse_float(value: str | None) -> float | None:
    """Parse float values from environment variables."""
    if value is None:
        return None
    return float(value)


def parse_csv(value: str | None) -> tuple[str, ...] | None:
    """Parse comma-separated values into a tuple of non-empty strings."""
    if value is None:
        return None
    return tuple(item.strip() for item in value.split(",") if item.strip())
