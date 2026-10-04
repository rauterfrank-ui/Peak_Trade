"""Single productive governed cycle step (delegates to canonical wallclock bridge)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Optional

from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.shadow_routing_v1 import (
    PreExternalProductiveEventV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.wallclock_hardening_binding_v2 import (
    run_hardened_wallclock_bridge_observation_cycle_v2,
)

ProductiveCycleStepFnV1 = Callable[
    [
        HardenedBridgeSessionStateV2,
        ObservationMarketTickV1,
        Decimal,
        float,
        str,
        int,
    ],
    "ProductiveCycleStepOutcomeV1",
]


@dataclass
class ProductiveCycleStepOutcomeV1:
    ok: bool
    productive_cycle_ran: bool
    bridge_cycle: dict[str, Any] | None
    pre_external_event: PreExternalProductiveEventV1 | None
    md_blockers: tuple[str, ...]
    fail_fatal: bool
    labels: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "productive_cycle_ran": self.productive_cycle_ran,
            "pre_external": self.pre_external_event is not None,
            "md_blockers": list(self.md_blockers),
            "fail_fatal": self.fail_fatal,
            "PRODUCTIVE_DECISION_LOGIC_DUPLICATION_COUNT": 0,
            "ORCHESTRATOR_SYNTHETIC_TRADING_DECISION_COUNT": 0,
        }


def run_hardened_bridge_productive_cycle_step_v1(
    bridge_state: HardenedBridgeSessionStateV2,
    tick: ObservationMarketTickV1,
    reference_price: Decimal,
    wall_now_unix: float,
    session_id: str,
    cycle_index: int,
) -> ProductiveCycleStepOutcomeV1:
    """Canonical productive wallclock path (same bridge as IPSO wallclock session)."""
    _ = cycle_index
    outcome = run_hardened_wallclock_bridge_observation_cycle_v2(
        bridge_state=bridge_state,
        ticks=[tick],
        reference_price=reference_price,
        wall_now_unix=wall_now_unix,
        session_id=session_id,
    )
    fatal = bool(
        outcome.md_blockers
        and any(
            str(b).startswith(("STALE_", "DATA_GAP", "OBSERVATION_FATAL"))
            for b in outcome.md_blockers
        )
    )
    return ProductiveCycleStepOutcomeV1(
        ok=outcome.ok,
        productive_cycle_ran=True,
        bridge_cycle=outcome.bridge_cycle,
        pre_external_event=None,
        md_blockers=tuple(outcome.md_blockers),
        fail_fatal=fatal and not outcome.ok,
        labels=dict(outcome.labels),
    )


def default_productive_cycle_step_v1(
    bridge_state: HardenedBridgeSessionStateV2,
    tick: ObservationMarketTickV1,
    reference_price: Decimal,
    wall_now_unix: float,
    session_id: str,
    cycle_index: int,
) -> ProductiveCycleStepOutcomeV1:
    return run_hardened_bridge_productive_cycle_step_v1(
        bridge_state,
        tick,
        reference_price,
        wall_now_unix,
        session_id,
        cycle_index,
    )
