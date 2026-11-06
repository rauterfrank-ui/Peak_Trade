"""Wallclock binding to hardened bridge v2 (no forced-wiring import).

Productive typed-volatility wiring edge:
  public mark observation
    → PT1M mark observation finalizer (session-local)
    → finalized PT1M mark sample (only on bucket close)
    → run_hardened_bridge_cycle_v2(finalized_pt1m_*)
    → CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional, Sequence

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
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    CAPABILITY_ID,
    OWNER,
    REQUIRED_TICKER_PRICE_FIELD,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    ensure_pt1m_mark_observation_finalizer_v1,
    run_hardened_bridge_cycle_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.market_data_price_basis_v2 import (
    build_explicit_mid_price_basis_v2,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)


@dataclass
class HardenedWallclockBridgeOutcomeV2:
    ok: bool
    bridge_cycle: Optional[dict[str, Any]] = None
    md_blockers: tuple[str, ...] = ()
    labels: dict[str, Any] = field(default_factory=dict)
    finalized_pt1m_emitted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "md_blockers": list(self.md_blockers),
            "labels": dict(self.labels),
            "bridge_cycle": self.bridge_cycle,
            "finalized_pt1m_emitted": self.finalized_pt1m_emitted,
        }


def run_hardened_wallclock_bridge_observation_cycle_v2(
    *,
    bridge_state: HardenedBridgeSessionStateV2,
    ticks: Sequence[ObservationMarketTickV1],
    reference_price: Decimal,
    wall_now_unix: float,
    session_id: str,
    price_field: str = REQUIRED_TICKER_PRICE_FIELD,
) -> HardenedWallclockBridgeOutcomeV2:
    params = MarketDataPolicyParamsV1(
        venue=VENUE_OKX,
        market_type=MARKET_TYPE_FUTURES,
        allowed_instruments=(CANONICAL_INSTRUMENT_ID,),
        network_allowed=False,
        wallclock_authorized_observe=True,
    )
    md = evaluate_market_data_sequence_v1(ticks, params=params, wall_now_unix=wall_now_unix)
    if not md.ok:
        return HardenedWallclockBridgeOutcomeV2(ok=False, md_blockers=tuple(md.blockers))

    mid = float(reference_price)
    event_ts = wall_now_unix
    receive_ts = wall_now_unix
    if ticks:
        mid = float(ticks[-1].mid_price)
        event_ts = float(ticks[-1].event_ts_unix)
        receive_ts = float(ticks[-1].receive_ts_unix)
    basis = build_explicit_mid_price_basis_v2(
        mid_price=mid,
        event_ts_unix=event_ts,
        receive_ts_unix=receive_ts,
        price_field=price_field,
    )

    # Productive typed-vol edge: finalize PT1M mark samples from distinct observations.
    # Decision cycles without a completed PT1M bucket do not invent vol observations.
    finalizer = ensure_pt1m_mark_observation_finalizer_v1(bridge_state)
    finalized = finalizer.observe_mark_v1(
        event_time_unix_seconds=event_ts,
        mark_price=mid,
        receive_time_unix_seconds=receive_ts,
    )
    finalized_kwargs: dict[str, Any] = {}
    finalized_emitted = False
    if finalized is not None:
        finalized_emitted = True
        transport = None
        if finalized.receive_time_unix_seconds is not None:
            transport = ObservationTransportMetadataV1(
                receive_time=float(finalized.receive_time_unix_seconds),
                wallclock_now=float(wall_now_unix),
            )
        finalized_kwargs = {
            "finalized_pt1m_mark_price": float(finalized.mark_price),
            "finalized_pt1m_event_time_unix_seconds": float(finalized.event_time_unix_seconds),
            "finalized_pt1m_transport": transport,
        }

    cycle = run_hardened_bridge_cycle_v2(
        bridge_state,
        mid_price=mid,
        event_ts_unix=wall_now_unix,
        session_id=session_id,
        price_basis=basis,
        **finalized_kwargs,
    )
    labels = {
        "execution_class": EXECUTION_CLASS_ANALYTICAL,
        "paper_execution": False,
        "orders_submitted": False,
        "credentials_used": False,
        "fills_are_analytical_simulated_only": True,
        "decision_economics_bridge": CAPABILITY_ID,
        "bridge_owner": OWNER,
        "hardening_v2": True,
        "hold_stub_bypassed": True,
        "ai_layer_non_authority": True,
        "ai_layer_can_override_decisions": False,
        "typed_volatility_pt1m_finalizer_wired": True,
        "finalized_pt1m_emitted": finalized_emitted,
        "pt1m_finalizer_finalized_count": finalizer.finalized_count,
    }
    return HardenedWallclockBridgeOutcomeV2(
        ok=True,
        bridge_cycle=cycle,
        labels=labels,
        finalized_pt1m_emitted=finalized_emitted,
    )
