from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NetworkGateDecision:
    ok: bool
    reason: str


def ensure_may_use_network_escalation(
    *,
    allow_network: bool,
    context: str = "telemetry",
    env_config: Optional[object] = None,
) -> None:
    """Deterministic enforcement for any outbound escalation.

    Default must deny when allow_network=True unless explicit gates are satisfied.
    Gates are config-based (no env vars): confirm_token + armed/enabled flags.
    """
    if not allow_network:
        return

    # Late imports to avoid import cycles.
    from src.core.environment import create_default_environment, LIVE_CONFIRM_TOKEN
    from src.live.safety import SafetyGuard

    cfg = env_config if env_config is not None else create_default_environment()

    guard = SafetyGuard(env_config=cfg)

    # Use the same live-gate primitives as PR-02: armed/enabled + confirm token.
    # Note: we do NOT require environment==LIVE here; live execution may be blocked by design,
    # but network escalation can still be gated with the same confirm-token discipline.
    if not getattr(cfg, "enable_live_trading", False):
        raise RuntimeError(
            f"Network escalation blocked: enable_live_trading=false (context={context})"
        )
    if not getattr(cfg, "live_mode_armed", False):
        raise RuntimeError(f"Network escalation blocked: live_mode_armed=false (context={context})")
    if getattr(cfg, "require_confirm_token", True):
        if getattr(cfg, "confirm_token", None) != LIVE_CONFIRM_TOKEN:
            raise RuntimeError(
                f"Network escalation blocked: confirm_token invalid/missing (context={context})"
            )

    # If SafetyGuard adds additional deterministic checks in the future, keep the contract centralized.
    return
