"""Shadow execution sink — SimulatedExecutionPort only; structurally no wire/credentials."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    TESTNET_AUTHORIZED,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
    construct_simulated_execution_port_v1,
)


@dataclass(frozen=True)
class ShadowExecutionRequestV1:
    instrument_id: str
    side: str
    quantity: str
    mark_price: str
    session_id: str
    cycle_index: int
    reduce_only: bool = False


@dataclass(frozen=True)
class ShadowExecutionEvidenceV1:
    REAL_POST_COUNT: int
    TESTNET_POST_COUNT: int
    WIRE_SEND_COUNT: int
    EXTERNAL_EFFECT_COUNT: int
    simulated_fill_present: bool
    port_kind: str
    lifecycle_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "REAL_POST_COUNT": self.REAL_POST_COUNT,
            "TESTNET_POST_COUNT": self.TESTNET_POST_COUNT,
            "WIRE_SEND_COUNT": self.WIRE_SEND_COUNT,
            "EXTERNAL_EFFECT_COUNT": self.EXTERNAL_EFFECT_COUNT,
            "simulated_fill_present": self.simulated_fill_present,
            "port_kind": self.port_kind,
            "lifecycle_state": self.lifecycle_state,
            "POST_ALLOWED": POST_ALLOWED,
            "REAL_VENUE_POST_ALLOWED": REAL_VENUE_POST_ALLOWED,
            "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED,
            "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
            "REAL_KEYCHAIN_ACCESS_AUTHORIZED": REAL_KEYCHAIN_ACCESS_AUTHORIZED,
        }


class ShadowExecutionSinkError(RuntimeError):
    pass


def execute_shadow_simulated_intent_v1(
    *,
    request: ShadowExecutionRequestV1,
    session: Any,
    portfolio: Any,
    state_root: Path | None = None,
    port: SimulatedExecutionPortV1 | None = None,
) -> tuple[dict[str, Any], ShadowExecutionEvidenceV1]:
    """Apply intended action through sole SimulatedExecutionPort (no external effect)."""
    if EXTERNAL_EFFECT_AUTHORIZED or POST_ALLOWED or REAL_VENUE_POST_ALLOWED:
        raise ShadowExecutionSinkError("standing_safety_flags_forbid_shadow_sink")
    sim_port = port or construct_simulated_execution_port_v1()
    if not isinstance(sim_port, SimulatedExecutionPortV1):
        raise ShadowExecutionSinkError("port_must_be_simulated_execution_port_v1")
    apply_out = sim_port.apply_intended_action(
        session=session,
        portfolio=portfolio,
        instrument_id=request.instrument_id,
        side=request.side,
        quantity=request.quantity,
        mark_price=Decimal(str(request.mark_price)),
        session_id=request.session_id,
        cycle_index=int(request.cycle_index),
        reduce_only=bool(request.reduce_only),
        state_root=state_root,
        persist=False,
    )
    fill_present = apply_out.get("fill") is not None
    lifecycle = "SIMULATED_FULL_FILL" if fill_present else "SIMULATED_NO_FILL"
    evidence = ShadowExecutionEvidenceV1(
        REAL_POST_COUNT=0,
        TESTNET_POST_COUNT=0,
        WIRE_SEND_COUNT=0,
        EXTERNAL_EFFECT_COUNT=0,
        simulated_fill_present=fill_present,
        port_kind=sim_port.PORT_KIND,
        lifecycle_state=lifecycle,
    )
    return apply_out, evidence
