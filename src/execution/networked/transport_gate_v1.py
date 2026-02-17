from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.execution.networked.entry_contract_v1 import (
    DENY_ENV,
    SECRET_ENV_HINTS,
    guard_entry_contract_v1,
)


class TransportGateError(RuntimeError):
    pass


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


def guard_transport_gate_v1(
    *,
    mode: str,
    dry_run: bool,
    adapter: str,
    intent: str,
    market: str,
    qty: float,
    transport_allow: Optional[str] = None,
) -> TransportDecisionV1:
    """
    Networked transport gate (v1).

    Current version is *networkless*: it always denies outbound network usage unless
    a future version explicitly enables it. This is a hard safety gate.

    - Enforces entry-contract guards (mode, dry_run, deny env, secret env)
    - Enforces transport_allow == "NO" (default). Any other value is denied.
    """
    # Reuse the entry contract gate as the first choke point
    guard_entry_contract_v1(
        mode=mode,
        dry_run=dry_run,
        adapter=adapter,
        intent=intent,
        market=market,
        qty=qty,
    )

    allow = (transport_allow or "NO").strip().upper()

    # v1 is networkless: only NO is permitted, anything else is denied
    if allow != "NO":
        raise TransportGateError(f"TRANSPORT_GATE_DENY transport_allow={allow}")

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
    )


def assert_networkless_v1() -> None:
    """
    Marker function to make intent explicit in code and tests.
    """
    return None


__all__ = [
    "DENY_ENV",
    "SECRET_ENV_HINTS",
    "TransportDecisionV1",
    "TransportGateError",
    "guard_transport_gate_v1",
    "assert_networkless_v1",
]
