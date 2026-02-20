from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class FeatureActivation:
    allow_double_play: bool
    allow_dynamic_leverage: bool
    reasons_double_play: Tuple[str, ...]
    reasons_dynamic_leverage: Tuple[str, ...]
    details: Dict[str, Any]


def _b(d: Dict[str, Any], k: str, default: bool = False) -> bool:
    return bool(d.get(k, default))


def evaluate_feature_activation(*, context: Dict[str, Any]) -> FeatureActivation:
    """
    SAFE DEFAULT OFF.
    Requires:
      - context.enabled True
      - context.armed True
      - confirm_token_present True (we avoid validating token here; we only check presence/flag)
      - feature-specific allow flags True
    """
    enabled = _b(context, "enabled", False)
    armed = _b(context, "armed", False)

    # Presence signal only; actual token validation remains in safety gate.
    confirm_ok = _b(context, "confirm_token_present", False) or _b(
        context, "confirm_token_valid", False
    )

    want_dp = _b(context, "allow_double_play", False)
    want_dl = _b(context, "allow_dynamic_leverage", False)

    rd = []
    rl = []

    if not enabled:
        rd.append("not_enabled")
        rl.append("not_enabled")
    if not armed:
        rd.append("not_armed")
        rl.append("not_armed")
    if not confirm_ok:
        rd.append("confirm_token_missing_or_invalid")
        rl.append("confirm_token_missing_or_invalid")

    allow_dp = bool(enabled and armed and confirm_ok and want_dp)
    allow_dl = bool(enabled and armed and confirm_ok and want_dl)

    if not want_dp:
        rd.append("allow_double_play_false")
    if not want_dl:
        rl.append("allow_dynamic_leverage_false")

    details = {
        "enabled": enabled,
        "armed": armed,
        "confirm_token_ok": confirm_ok,
        "allow_double_play": allow_dp,
        "allow_dynamic_leverage": allow_dl,
        "reasons": {"double_play": rd, "dynamic_leverage": rl},
    }

    return FeatureActivation(
        allow_double_play=allow_dp,
        allow_dynamic_leverage=allow_dl,
        reasons_double_play=tuple(rd),
        reasons_dynamic_leverage=tuple(rl),
        details=details,
    )
