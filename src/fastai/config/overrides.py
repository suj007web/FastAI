"""Constructor override extraction helpers."""

from __future__ import annotations

OverrideMap = dict[str, object]


def override_str(overrides: OverrideMap, key: str, *aliases: str) -> str | None:
    """Extract string override from key aliases."""
    for candidate in (key, *aliases):
        value = overrides.get(candidate)
        if isinstance(value, str):
            return value
    return None


def override_int(overrides: OverrideMap, key: str, *aliases: str) -> int | None:
    """Extract integer override from key aliases."""
    for candidate in (key, *aliases):
        value = overrides.get(candidate)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def override_float(overrides: OverrideMap, key: str, *aliases: str) -> float | None:
    """Extract numeric override and normalize to float."""
    for candidate in (key, *aliases):
        value = overrides.get(candidate)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def override_bool(overrides: OverrideMap, key: str, *aliases: str) -> bool | None:
    """Extract boolean override from key aliases."""
    for candidate in (key, *aliases):
        value = overrides.get(candidate)
        if isinstance(value, bool):
            return value
    return None


def override_csv(overrides: OverrideMap, key: str, *aliases: str) -> tuple[str, ...] | None:
    """Extract sequence override and normalize to tuple[str, ...]."""
    for candidate in (key, *aliases):
        value = overrides.get(candidate)
        if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
            return value
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return tuple(value)
    return None
