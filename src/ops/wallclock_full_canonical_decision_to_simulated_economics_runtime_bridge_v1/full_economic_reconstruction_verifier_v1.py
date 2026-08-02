"""Full economic reconstruction verifier for wallclock bridge evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    CAPABILITY_ID,
    EXECUTION_CLASS_ANALYTICAL,
    OWNER,
)

VERIFIER_ID = f"{OWNER}.full_economic_reconstruction_verifier_v1"


@dataclass
class FullEconomicReconstructionResultV1:
    ok: bool
    verifier_id: str
    capability_id: str
    blockers: list[str] = field(default_factory=list)
    reconstructed_fill_count: int = 0
    reconstructed_equity: str = "0"
    expected_equity: str = "0"
    reconstructed_fees: str = "0"
    expected_fees: str = "0"
    call_graph_complete: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_CALL_GRAPH: tuple[str, ...] = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "okx_public_market_data",
    "feature_pipeline",
    "regime_pipeline",
    "master_v2_double_play_integrated_offline_replay",
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
    "analytical_simulated_execution",
    "simulated_fill_fee_slippage",
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    "simulated_economics_no_order_path",
    "evidence",
    "full_economic_reconstruction_verifier",
)


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


def verify_full_economic_reconstruction_v1(
    *,
    cycle_ledger: Sequence[Mapping[str, Any]],
    fill_ledger: Sequence[Mapping[str, Any]] | None = None,
    final_portfolio_snapshot: Mapping[str, Any] | None = None,
    initial_equity: Decimal | None = None,
) -> FullEconomicReconstructionResultV1:
    """Re-apply intended actions and compare portfolio economics fail-closed."""
    blockers: list[str] = []
    notes: list[str] = []
    if not cycle_ledger:
        return FullEconomicReconstructionResultV1(
            ok=False,
            verifier_id=VERIFIER_ID,
            capability_id=CAPABILITY_ID,
            blockers=["EMPTY_CYCLE_LEDGER"],
        )

    # Call-graph completeness from last cycle (or any cycle that claims full graph).
    graphs = [tuple(c.get("call_graph") or ()) for c in cycle_ledger]
    call_graph_complete = any(all(node in g for node in REQUIRED_CALL_GRAPH) for g in graphs)
    if not call_graph_complete:
        blockers.append("CALL_GRAPH_INCOMPLETE")

    for i, cycle in enumerate(cycle_ledger):
        if cycle.get("orders_authorized") is True:
            blockers.append(f"ORDERS_AUTHORIZED_TRUE_CYCLE_{i}")
        if cycle.get("live_authorized") is True:
            blockers.append(f"LIVE_AUTHORIZED_TRUE_CYCLE_{i}")
        if cycle.get("testnet_authorized") is True:
            blockers.append(f"TESTNET_AUTHORIZED_TRUE_CYCLE_{i}")
        if cycle.get("execution_eligible") is True:
            blockers.append(f"EXECUTION_ELIGIBLE_TRUE_CYCLE_{i}")
        if cycle.get("economic_validity_pass") is True:
            blockers.append(f"ECONOMIC_VALIDITY_PASS_TRUE_CYCLE_{i}")
        if cycle.get("promotion_pass") is True:
            blockers.append(f"PROMOTION_PASS_TRUE_CYCLE_{i}")
        if cycle.get("runtime_bridge_live_activated") is True:
            blockers.append(f"RUNTIME_BRIDGE_LIVE_ACTIVATED_TRUE_CYCLE_{i}")
        if str(cycle.get("execution_class") or "") != EXECUTION_CLASS_ANALYTICAL:
            blockers.append(f"EXECUTION_CLASS_MISMATCH_CYCLE_{i}")
        if not cycle.get("decision_authority_owner"):
            blockers.append(f"MISSING_DECISION_AUTHORITY_OWNER_CYCLE_{i}")
        if "feature_regime" not in cycle:
            blockers.append(f"MISSING_FEATURE_REGIME_CYCLE_{i}")
        if "intended_action" not in cycle:
            blockers.append(f"MISSING_INTENDED_ACTION_CYCLE_{i}")

    eq0 = initial_equity
    if eq0 is None and final_portfolio_snapshot:
        params = (final_portfolio_snapshot.get("params") or {}).get("initial_equity")
        if params is not None:
            eq0 = _dec(params)
    if eq0 is None:
        eq0 = Decimal("100000")

    model = SimulatedPortfolioEconomicsModelV1(PortfolioEconomicsModelParamsV1(initial_equity=eq0))
    reconstructed_fills = 0
    for cycle in cycle_ledger:
        action = cycle.get("intended_action") or {}
        side = str(action.get("intended_side") or "HOLD")
        qty = _dec(action.get("intended_quantity") or "0")
        fr = cycle.get("feature_regime") or {}
        mark = _dec(fr.get("mark_price") or "0")
        if mark <= 0:
            blockers.append("MARK_PRICE_MISSING_FOR_RECONSTRUCTION")
            continue
        instrument_id = str(cycle.get("instrument_id") or "")
        fill = model.apply_intended_action(
            instrument_id=instrument_id,
            side=side,
            quantity=qty if side in {"BUY", "SELL"} else Decimal("0"),
            mark_price=mark,
        )
        if fill is not None:
            reconstructed_fills += 1

    metrics = model.economic_metrics()
    expected_equity = None
    expected_fees = None
    if final_portfolio_snapshot:
        state = final_portfolio_snapshot.get("state") or {}
        expected_equity = state.get("equity")
        expected_fees = state.get("cumulative_fees")
        em = final_portfolio_snapshot.get("economic_metrics") or {}
        if expected_equity is None:
            expected_equity = em.get("equity")
        if expected_fees is None:
            expected_fees = em.get("fees")

    if expected_equity is not None and _dec(expected_equity) != metrics.equity:
        blockers.append(
            f"EQUITY_MISMATCH:reconstructed={metrics.equity}:expected={expected_equity}"
        )
    if expected_fees is not None and _dec(expected_fees) != metrics.fees:
        blockers.append(f"FEES_MISMATCH:reconstructed={metrics.fees}:expected={expected_fees}")

    if fill_ledger is not None and len(fill_ledger) != reconstructed_fills:
        # Allow MTM-only cycles with no fills; ledger length must match reconstructed fills.
        blockers.append(
            f"FILL_COUNT_MISMATCH:ledger={len(fill_ledger)}:reconstructed={reconstructed_fills}"
        )

    notes.append(f"cycles={len(cycle_ledger)}")
    notes.append(f"reconstructed_fills={reconstructed_fills}")
    return FullEconomicReconstructionResultV1(
        ok=not blockers,
        verifier_id=VERIFIER_ID,
        capability_id=CAPABILITY_ID,
        blockers=blockers,
        reconstructed_fill_count=reconstructed_fills,
        reconstructed_equity=str(metrics.equity),
        expected_equity=str(expected_equity) if expected_equity is not None else "",
        reconstructed_fees=str(metrics.fees),
        expected_fees=str(expected_fees) if expected_fees is not None else "",
        call_graph_complete=call_graph_complete,
        notes=notes,
    )


def verify_bridge_evidence_root_v1(*, evidence_root: Path) -> FullEconomicReconstructionResultV1:
    root = Path(evidence_root)
    cycle_path = root / "bridge_cycle_ledger.jsonl"
    fill_path = root / "bridge_fill_ledger.jsonl"
    portfolio_path = root / "portfolio_snapshot.json"
    if not cycle_path.is_file():
        return FullEconomicReconstructionResultV1(
            ok=False,
            verifier_id=VERIFIER_ID,
            capability_id=CAPABILITY_ID,
            blockers=["MISSING_BRIDGE_CYCLE_LEDGER"],
        )
    cycles: list[dict[str, Any]] = []
    for line in cycle_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cycles.append(json.loads(line))
    fills: list[dict[str, Any]] = []
    if fill_path.is_file():
        for line in fill_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                fills.append(json.loads(line))
    portfolio = None
    if portfolio_path.is_file():
        portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
    return verify_full_economic_reconstruction_v1(
        cycle_ledger=cycles,
        fill_ledger=fills,
        final_portfolio_snapshot=portfolio,
    )
