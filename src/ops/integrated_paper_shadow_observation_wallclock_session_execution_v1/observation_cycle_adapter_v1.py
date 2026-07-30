"""Adapt IPSO observation cycle for wallclock MD ticks (analytical only)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Optional, Sequence

from src.ops.integrated_paper_shadow_observation_session_v1.entrypoint_v1 import (
    ObservationCycleResultV1,
    run_integrated_paper_shadow_observation_cycle_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    MarketDataPolicyParamsV1,
    ObservationMarketTickV1,
    evaluate_market_data_sequence_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    EXECUTION_CLASS_ANALYTICAL,
    MARKET_TYPE_FUTURES,
    VENUE_OKX,
)


@dataclass
class WallclockObservationCycleOutcomeV1:
    ok: bool
    cycle: Optional[ObservationCycleResultV1] = None
    md_blockers: tuple[str, ...] = ()
    labels: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "md_blockers": list(self.md_blockers),
            "labels": dict(self.labels),
            "cycle": None if self.cycle is None else self.cycle.to_dict(),
        }


def run_wallclock_observation_cycle_v1(
    *,
    ticks: Sequence[ObservationMarketTickV1],
    reference_price: Decimal,
    wall_now_unix: float,
    intended_side: str,
    intended_quantity: Decimal,
) -> WallclockObservationCycleOutcomeV1:
    """Validate ticks then run offline observation cycle (no network inside).

    Defaults for HOLD / quantity=0 are intentionally absent. Callers must supply
    explicit intended_side and intended_quantity with strategy provenance. The
    productive wallclock path does not call this adapter when the decision→economics
    bridge is required (fail-closed BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE).
    """
    if not str(intended_side).strip():
        raise ValueError("INTENDED_SIDE_REQUIRED_NO_DEFAULT_HOLD")
    params = MarketDataPolicyParamsV1(
        venue=VENUE_OKX,
        market_type=MARKET_TYPE_FUTURES,
        allowed_instruments=(CANONICAL_INSTRUMENT_ID,),
        network_allowed=False,  # tick validation is offline; transport already fetched
        wallclock_authorized_observe=True,
    )
    md = evaluate_market_data_sequence_v1(ticks, params=params, wall_now_unix=wall_now_unix)
    if not md.ok:
        return WallclockObservationCycleOutcomeV1(ok=False, md_blockers=tuple(md.blockers))

    cycle = run_integrated_paper_shadow_observation_cycle_v1(
        mode="observation",
        instrument_id=CANONICAL_INSTRUMENT_ID,
        ticks=ticks,
        reference_price=reference_price,
        intended_side=intended_side,
        intended_quantity=intended_quantity,
        orders_enabled=False,
        broker_writes_enabled=False,
        live_enabled=False,
        testnet_enabled=False,
        network_enabled=False,  # cycle itself remains offline
        credentials_enabled=False,
    )
    labels = {
        "execution_class": EXECUTION_CLASS_ANALYTICAL,
        "paper_execution": False,
        "orders_submitted": False,
        "credentials_used": False,
        "fills_are_analytical_simulated_only": True,
        "default_hold_fallback_active": False,
        "default_zero_quantity_fallback_active": False,
    }
    return WallclockObservationCycleOutcomeV1(
        ok=cycle.terminal_status == "PASS",
        cycle=cycle,
        labels=labels,
    )
