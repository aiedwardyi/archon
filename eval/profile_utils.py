from __future__ import annotations

import copy
from typing import Any


def apply_profile(config: dict[str, Any], profile_name: str | None = None) -> dict[str, Any]:
    """Return a config dict with the selected named profile merged in.

    Profiles are shallow overlays with optional inheritance via ``extends``.
    Base config values remain the default when a profile does not override them.
    """

    merged = copy.deepcopy(config)
    profiles = merged.get("profiles") or {}
    selected = profile_name or merged.get("default_profile")
    if not selected:
        merged["_active_profile"] = None
        merged["_applied_profiles"] = []
        return merged

    if selected not in profiles:
        raise ValueError(f"Unknown eval profile '{selected}'")

    applied: list[str] = []
    visiting: set[str] = set()

    def _merge(name: str) -> None:
        if name in applied:
            return
        if name in visiting:
            raise ValueError(f"Cyclic eval profile inheritance involving '{name}'")
        profile = profiles.get(name)
        if not isinstance(profile, dict):
            raise ValueError(f"Eval profile '{name}' must be an object")
        visiting.add(name)
        parent = profile.get("extends")
        if parent:
            _merge(str(parent))
        for key, value in profile.items():
            if key == "extends":
                continue
            merged[key] = copy.deepcopy(value)
        visiting.remove(name)
        applied.append(name)

    _merge(selected)
    merged["_active_profile"] = selected
    merged["_applied_profiles"] = applied
    return merged
