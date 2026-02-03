from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkGateDecision:
    ok: bool
    reason: str


def ensure_may_use_network_escalation(*, allow_network: bool, context: str = "telemetry") -> None:
    """
    Deterministic enforcement for any outbound escalation.
    Default must deny when allow_network=True unless explicit live gates are satisfied.

    PR-10: implement by wiring to existing environment/safety config (confirm token, armed/enabled, phase).
    """
    if not allow_network:
        return
    raise RuntimeError(
        f"Network escalation blocked (allow_network=true) for context={context} (PR-10 not wired yet)"
    )
