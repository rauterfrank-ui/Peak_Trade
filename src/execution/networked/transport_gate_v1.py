from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

from src.execution.networked.canary_live_gate_v1 import (
    CanaryLiveGateDecisionV1,
    evaluate_canary_live_gate_v1_from_environ,
)
from src.execution.networked.entry_contract_v1 import (
    DENY_ENV,
    SECRET_ENV_HINTS,
    guard_entry_contract_v1,
)


class TransportGateError(RuntimeError):
    pass


@dataclass(frozen=True)
class TransportGateV1:
    """Config for transport gate (transport_allow only; v1 networkless)."""

    transport_allow: str = "NO"


@dataclass(frozen=True)
class TransportDecisionV1:
    ok: bool
    reason: str
    mode: str
    dry_run: bool
    transport_allow: str
    adapter: str
    intent: str
    market: str
    qty: float
    # LB-EXE-001: explicit canary/live preconditions; v1 always denies outbound (audit field).
    canary_live_gate_v1: Optional[CanaryLiveGateDecisionV1] = None


def guard_transport_gate_v1(
    *,
    mode: str,
    dry_run: bool,
    adapter: str,
    intent: str,
    market: str,
    qty: float,
    transport_allow: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> TransportDecisionV1:
    """
    Networked transport gate (v1).

    Current version is *networkless*: it always denies outbound network usage unless
    a future version explicitly enables it. This is a hard safety gate.

    - Enforces entry-contract guards (mode, dry_run, deny env, secret env)
    - Enforces transport_allow == "NO" (default). Any other value is denied.

    ``env`` is forwarded to :func:`~src.execution.networked.entry_contract_v1.guard_entry_contract_v1`
    (default: process environment). The same resolved mapping is passed to the canary gate
    (``env or dict(os.environ)``). Tests may pass an empty mapping to isolate from host env.
    """
    # Reuse the entry contract gate as the first choke point
    guard_entry_contract_v1(
        mode=mode,
        dry_run=dry_run,
        adapter=adapter,
        intent=intent,
        market=market,
        qty=qty,
        env=env,
    )

    allow = (transport_allow or "NO").strip().upper()

    # v1 is networkless: NO always permitted; YES only when mode in shadow/paper and dry_run
    if allow == "YES":
        if mode not in ("shadow", "paper"):
            raise TransportGateError(
                f"TRANSPORT_GATE_DENY transport_allow=YES requires mode in (shadow,paper), got {mode}"
            )
        if not dry_run:
            raise TransportGateError(
                "TRANSPORT_GATE_DENY transport_allow=YES requires dry_run=True"
            )
    elif allow != "NO":
        raise TransportGateError(f"TRANSPORT_GATE_DENY transport_allow={allow}")

    # Match :func:`guard_entry_contract_v1` env resolution so canary sees the same mapping
    # as entry validation (``env or dict(os.environ)``).
    resolved_env = env or dict(os.environ)
    canary = evaluate_canary_live_gate_v1_from_environ(
        dry_run=dry_run,
        mode=mode,
        environ=resolved_env,
    )

    return TransportDecisionV1(
        ok=True,
        reason="NETWORKLESS_V1",
        mode=mode,
        dry_run=dry_run,
        transport_allow=allow,
        adapter=adapter,
        intent=intent,
        market=market,
        qty=qty,
        canary_live_gate_v1=canary,
    )


def assert_networkless_v1() -> None:
    """
    Marker function to make intent explicit in code and tests.
    """
    return None


__all__ = [
    "CanaryLiveGateDecisionV1",
    "DENY_ENV",
    "SECRET_ENV_HINTS",
    "TransportDecisionV1",
    "TransportGateError",
    "TransportGateV1",
    "guard_transport_gate_v1",
    "assert_networkless_v1",
]
