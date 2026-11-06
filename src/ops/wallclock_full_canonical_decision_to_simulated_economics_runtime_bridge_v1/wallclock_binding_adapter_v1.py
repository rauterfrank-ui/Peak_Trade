"""Bind wallclock MD observation cycles to the decision→economics bridge."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
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
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeCycleResultV1,
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    verify_full_economic_reconstruction_v1,
)


@dataclass
class WallclockBridgeCycleOutcomeV1:
    ok: bool
    bridge_cycle: Optional[BridgeCycleResultV1] = None
    md_blockers: tuple[str, ...] = ()
    labels: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "md_blockers": list(self.md_blockers),
            "labels": dict(self.labels),
            "bridge_cycle": None if self.bridge_cycle is None else self.bridge_cycle.to_dict(),
        }


def run_wallclock_bridge_observation_cycle_v1(
    *,
    bridge_state: BridgeSessionStateV1,
    ticks: Sequence[ObservationMarketTickV1],
    reference_price: Decimal,
    wall_now_unix: float,
    session_id: str,
) -> WallclockBridgeCycleOutcomeV1:
    """Validate MD ticks then run full decision→economics bridge cycle."""
    params = MarketDataPolicyParamsV1(
        venue=VENUE_OKX,
        market_type=MARKET_TYPE_FUTURES,
        allowed_instruments=(CANONICAL_INSTRUMENT_ID,),
        network_allowed=False,
        wallclock_authorized_observe=True,
    )
    md = evaluate_market_data_sequence_v1(ticks, params=params, wall_now_unix=wall_now_unix)
    if not md.ok:
        return WallclockBridgeCycleOutcomeV1(ok=False, md_blockers=tuple(md.blockers))

    mid = float(reference_price)
    if ticks:
        mid = float(ticks[-1].mid_price)
    cycle = run_bridge_cycle_v1(
        bridge_state,
        mid_price=mid,
        event_ts_unix=wall_now_unix,
        session_id=session_id,
    )
    labels = {
        "execution_class": EXECUTION_CLASS_ANALYTICAL,
        "paper_execution": False,
        "orders_submitted": False,
        "credentials_used": False,
        "fills_are_analytical_simulated_only": True,
        "decision_economics_bridge": CAPABILITY_ID,
        "bridge_owner": OWNER,
        "hold_stub_bypassed": True,
    }
    return WallclockBridgeCycleOutcomeV1(ok=True, bridge_cycle=cycle, labels=labels)


def persist_bridge_session_evidence_v1(
    *,
    evidence_root: Path,
    bridge_state: BridgeSessionStateV1,
    append_event,
    write_immutable_json,
) -> dict[str, Any]:
    """Write cycle/fill ledgers + portfolio economics and run reconstruction verifier."""
    root = Path(evidence_root)
    for cycle in bridge_state.cycle_ledger:
        append_event("bridge_cycle_ledger.jsonl", cycle)
        append_event(
            "decision_trace.jsonl",
            {
                "cycle": cycle.get("cycle_index"),
                "decision_result": cycle.get("decision_outcome"),
                "direction": cycle.get("direction"),
                "selected_side": cycle.get("selected_side"),
                "intended_action": cycle.get("intended_action"),
                "feature_regime": cycle.get("feature_regime"),
                "labels": {"bridge": CAPABILITY_ID},
            },
        )
        append_event(
            "risk_telemetry.jsonl",
            {
                "cycle": cycle.get("cycle_index"),
                "risk_sizing_result": cycle.get("risk_sizing_result"),
                "safety_result": cycle.get("safety_result"),
            },
        )
    for fill in bridge_state.fill_ledger:
        append_event("bridge_fill_ledger.jsonl", fill)
        append_event("simulated_fills.jsonl", fill)

    portfolio = dict(bridge_state.portfolio.snapshot())
    metrics = bridge_state.portfolio.economic_metrics().to_dict()
    write_immutable_json("portfolio_snapshot.json", portfolio)
    write_immutable_json(
        "economic_metrics.json",
        {
            **metrics,
            "execution_class": EXECUTION_CLASS_ANALYTICAL,
            "analytical_only": True,
            "bridge_capability_id": CAPABILITY_ID,
            "stub": False,
        },
    )
    verification = verify_full_economic_reconstruction_v1(
        cycle_ledger=bridge_state.cycle_ledger,
        fill_ledger=bridge_state.fill_ledger,
        final_portfolio_snapshot=portfolio,
    )
    write_immutable_json(
        "full_economic_reconstruction_verifier.json",
        verification.to_dict(),
    )
    # Ensure verifier node present on last cycle evidence for reconstruction checks.
    if bridge_state.cycle_ledger:
        # already included in CALL_GRAPH_V1
        pass
    return verification.to_dict()
