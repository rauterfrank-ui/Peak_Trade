from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from src.risk.dynamic_leverage import DynamicLeverageConfig, compute_dynamic_leverage


@dataclass(frozen=True)
class DynamicLeverageLiveDecision:
    enabled: bool
    strength: float
    leverage: Optional[float]
    reasons: Tuple[str, ...]
    details: Dict[str, Any]


def _get_bool(d: Dict[str, Any], key: str, default: bool) -> bool:
    v = d.get(key, default)
    return bool(v)


def evaluate_dynamic_leverage_for_live(*, context: Dict[str, Any]) -> DynamicLeverageLiveDecision:
    """
    SAFE DEFAULT OFF.
    - If not enabled -> return enabled=False and no leverage.
    - If enabled -> compute leverage using contract; attach details; never raises outward.
    """
    reasons = []
    details: Dict[str, Any] = {}

    enabled = _get_bool(context, "dynamic_leverage_enabled", False)
    strength_raw = context.get("strength", 0.0)

    try:
        strength = float(strength_raw)
    except Exception:
        strength = 0.0
        reasons.append("strength_invalid_defaulted")

    if not enabled:
        details.update({"enabled": False, "strength": max(0.0, min(1.0, strength)), "cap": 50.0})
        return DynamicLeverageLiveDecision(False, strength, None, tuple(reasons), details)

    cfg_d = context.get("dynamic_leverage_cfg", {}) or {}
    try:
        cfg = DynamicLeverageConfig(
            min_leverage=float(cfg_d.get("min_leverage", 1.0)),
            max_leverage=float(cfg_d.get("max_leverage", 50.0)),
            gamma=float(cfg_d.get("gamma", 2.0)),
        )
        lv = compute_dynamic_leverage(strength=strength, cfg=cfg)
        details.update(
            {
                "enabled": True,
                "strength": max(0.0, min(1.0, strength)),
                "leverage": float(lv),
                "min_leverage": float(cfg.min_leverage),
                "cap": float(cfg.max_leverage),
                "gamma": float(cfg.gamma),
            }
        )
        return DynamicLeverageLiveDecision(True, strength, float(lv), tuple(reasons), details)
    except Exception as e:
        # fail-closed: do not enable sizing if config invalid
        reasons.append(f"dynamic_leverage_exception:{type(e).__name__}")
        details.update({"enabled": False, "strength": max(0.0, min(1.0, strength)), "cap": 50.0})
        return DynamicLeverageLiveDecision(False, strength, None, tuple(reasons), details)
