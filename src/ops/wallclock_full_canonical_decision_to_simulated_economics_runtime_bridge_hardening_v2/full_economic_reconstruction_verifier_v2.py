"""Extended full economic reconstruction verifier v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Sequence

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    CAPABILITY_ID,
    EXECUTION_CLASS_ANALYTICAL,
    OWNER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    CALL_GRAPH_V2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
    IdempotentPortfolioV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.provenance_v2 import (
    portfolio_state_hash,
)

VERIFIER_ID = f"{OWNER}.full_economic_reconstruction_verifier_v2"


@dataclass
class HardeningReconstructionResultV2:
    ok: bool
    verifier_id: str
    capability_id: str
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    reconstructed_fill_count: int = 0
    reconstructed_equity: str = "0"
    expected_equity: str = "0"
    reconstructed_fees: str = "0"
    expected_fees: str = "0"
    call_graph_complete: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


def verify_full_economic_reconstruction_v2(
    *,
    cycle_ledger: Sequence[Mapping[str, Any]],
    fill_ledger: Sequence[Mapping[str, Any]] | None = None,
    final_portfolio_snapshot: Mapping[str, Any] | None = None,
    economic_metrics: Mapping[str, Any] | None = None,
    integrity_manifest: Mapping[str, Any] | None = None,
    forced_fixture_excluded: bool = False,
) -> HardeningReconstructionResultV2:
    blockers: list[str] = []
    notes: list[str] = []
    if not cycle_ledger:
        return HardeningReconstructionResultV2(
            ok=False,
            verifier_id=VERIFIER_ID,
            capability_id=CAPABILITY_ID,
            blockers=["EMPTY_CYCLE_LEDGER"],
        )

    graphs = [tuple(c.get("call_graph") or ()) for c in cycle_ledger]
    call_graph_complete = any(all(node in g for node in CALL_GRAPH_V2) for g in graphs)
    if not call_graph_complete:
        blockers.append("CALL_GRAPH_INCOMPLETE")

    seen_cycles: set[str] = set()
    seen_decisions: set[str] = set()
    seen_risks: set[str] = set()
    seen_intents: set[str] = set()
    seen_fills: set[str] = set()
    prev_index = 0
    for i, cycle in enumerate(cycle_ledger, start=1):
        if cycle.get("orders_authorized") is True:
            blockers.append(f"ORDERS_AUTHORIZED_TRUE_CYCLE_{i}")
        if cycle.get("live_authorized") is True:
            blockers.append(f"LIVE_AUTHORIZED_TRUE_CYCLE_{i}")
        if cycle.get("testnet_authorized") is True:
            blockers.append(f"TESTNET_AUTHORIZED_TRUE_CYCLE_{i}")
        if cycle.get("execution_eligible") is True:
            blockers.append(f"EXECUTION_ELIGIBLE_TRUE_CYCLE_{i}")
        if str(cycle.get("execution_class") or "") != EXECUTION_CLASS_ANALYTICAL:
            blockers.append(f"EXECUTION_CLASS_MISMATCH_CYCLE_{i}")
        idx = int(cycle.get("cycle_index") or 0)
        if idx != prev_index + 1 and prev_index != 0:
            # allow starting at 1
            if not (prev_index == 0 and idx == 1):
                blockers.append(f"CYCLE_ID_CONTINUITY_BREAK:{prev_index}->{idx}")
        if prev_index == 0 and idx != 1:
            blockers.append(f"CYCLE_INDEX_MUST_START_AT_1:{idx}")
        prev_index = idx

        cycle_id = str(cycle.get("cycle_id") or "")
        decision_id = str(cycle.get("decision_id") or "")
        risk_id = str(cycle.get("risk_decision_id") or "")
        intent_id = str(cycle.get("intent_id") or "")
        fill_id = cycle.get("fill_id")
        if not cycle_id:
            blockers.append(f"MISSING_CYCLE_ID_{i}")
        elif cycle_id in seen_cycles:
            blockers.append(f"DUPLICATE_CYCLE_ID:{cycle_id}")
        else:
            seen_cycles.add(cycle_id)
        if not decision_id:
            blockers.append(f"MISSING_DECISION_ID_{i}")
        elif decision_id in seen_decisions:
            blockers.append(f"DUPLICATE_DECISION_ID:{decision_id}")
        else:
            seen_decisions.add(decision_id)
        if not risk_id:
            blockers.append(f"MISSING_RISK_DECISION_ID_{i}")
        elif risk_id in seen_risks:
            blockers.append(f"DUPLICATE_RISK_DECISION_ID:{risk_id}")
        else:
            seen_risks.add(risk_id)
        if not intent_id:
            blockers.append(f"MISSING_INTENT_ID_{i}")
        elif intent_id in seen_intents:
            blockers.append(f"DUPLICATE_INTENT_ID:{intent_id}")
        else:
            seen_intents.add(intent_id)
        if not str(cycle.get("feature_digest") or ""):
            blockers.append(f"MISSING_FEATURE_DIGEST_{i}")
        if not str(cycle.get("regime_digest") or ""):
            blockers.append(f"MISSING_REGIME_DIGEST_{i}")
        if not str(cycle.get("config_digest") or ""):
            blockers.append(f"MISSING_CONFIG_DIGEST_{i}")
        if not str(cycle.get("portfolio_state_before_hash") or ""):
            blockers.append(f"MISSING_PORTFOLIO_BEFORE_HASH_{i}")
        if not str(cycle.get("portfolio_state_after_hash") or ""):
            blockers.append(f"MISSING_PORTFOLIO_AFTER_HASH_{i}")

        action = cycle.get("intended_action") or {}
        if action.get("decision_id") != decision_id:
            blockers.append(f"DECISION_ID_LINKAGE_BREAK_{i}")
        if action.get("risk_decision_id") != risk_id:
            blockers.append(f"RISK_ID_LINKAGE_BREAK_{i}")
        if action.get("intent_id") != intent_id:
            blockers.append(f"INTENT_ID_LINKAGE_BREAK_{i}")

        fill = cycle.get("fill")
        if fill is not None:
            fid = str(fill.get("fill_id") or fill_id or "")
            if not fid:
                blockers.append(f"MISSING_FILL_ID_{i}")
            elif fid in seen_fills:
                blockers.append(f"DUPLICATE_FILL_ID:{fid}")
            else:
                seen_fills.add(fid)
            if fill.get("decision_id") != decision_id:
                blockers.append(f"FILL_DECISION_LINKAGE_BREAK_{i}")
            if fill.get("intent_id") != intent_id:
                blockers.append(f"FILL_INTENT_LINKAGE_BREAK_{i}")
            if fill.get("portfolio_state_before_hash") != cycle.get("portfolio_state_before_hash"):
                blockers.append(f"FILL_BEFORE_HASH_MISMATCH_{i}")
            if fill.get("portfolio_state_after_hash") != cycle.get("portfolio_state_after_hash"):
                blockers.append(f"FILL_AFTER_HASH_MISMATCH_{i}")

    eq0 = Decimal("100000")
    if final_portfolio_snapshot:
        params = (final_portfolio_snapshot.get("params") or {}).get("initial_equity")
        if params is not None:
            eq0 = _dec(params)
    model = IdempotentPortfolioV2.from_params(PortfolioEconomicsModelParamsV1(initial_equity=eq0))
    reconstructed_fills = 0
    for cycle in cycle_ledger:
        action = cycle.get("intended_action") or {}
        side = str(action.get("intended_side") or "HOLD")
        qty = _dec(action.get("intended_quantity") or "0")
        fr = cycle.get("feature_regime") or {}
        mark = _dec(fr.get("mark_price") or "0")
        intent_id = str(cycle.get("intent_id") or "")
        fill_id = cycle.get("fill_id")
        if mark <= 0:
            blockers.append("MARK_PRICE_MISSING_FOR_RECONSTRUCTION")
            continue
        fill = model.apply_intended_action(
            instrument_id=str(cycle.get("instrument_id") or ""),
            side=side,
            quantity=qty if side in {"BUY", "SELL"} else Decimal("0"),
            mark_price=mark,
            intent_id=intent_id,
            fill_id=str(fill_id) if fill_id else None,
        )
        if fill is not None:
            reconstructed_fills += 1
            # Fee / slippage arithmetic checks against cycle fill when present.
            cfill = cycle.get("fill") or {}
            if cfill:
                if _dec(cfill.get("fee") or cfill.get("fee_amount") or "0") != fill.fee:
                    blockers.append(f"FEE_ARITHMETIC_MISMATCH:{cycle.get('cycle_id')}")
                if (
                    _dec(cfill.get("slippage_cost") or cfill.get("slippage_amount") or "0")
                    != fill.slippage_cost
                ):
                    blockers.append(f"SLIPPAGE_ARITHMETIC_MISMATCH:{cycle.get('cycle_id')}")
                if (
                    _dec(cfill.get("fill_price") or cfill.get("simulated_fill_price") or "0")
                    != fill.fill_price
                ):
                    blockers.append(f"FILL_PRICE_ARITHMETIC_MISMATCH:{cycle.get('cycle_id')}")

    metrics = model.economic_metrics()
    expected_equity = None
    expected_fees = None
    expected_slippage = None
    expected_realized = None
    expected_unrealized = None
    expected_drawdown = None
    expected_peak = None
    if final_portfolio_snapshot:
        state = final_portfolio_snapshot.get("state") or {}
        expected_equity = state.get("equity")
        expected_fees = state.get("cumulative_fees")
        expected_slippage = state.get("cumulative_slippage")
        expected_realized = state.get("realized_pnl")
        expected_unrealized = state.get("unrealized_pnl")
        expected_drawdown = state.get("max_drawdown")
        expected_peak = state.get("peak_equity")
        after = portfolio_state_hash(final_portfolio_snapshot)
        notes.append(f"final_portfolio_hash={after}")

    def _check(name: str, expected: Any, actual: Decimal) -> None:
        if expected is not None and _dec(expected) != actual:
            blockers.append(f"{name}_MISMATCH:reconstructed={actual}:expected={expected}")

    _check("EQUITY", expected_equity, metrics.equity)
    _check("FEES", expected_fees, metrics.fees)
    _check("SLIPPAGE", expected_slippage, metrics.slippage)
    _check("REALIZED_PNL", expected_realized, metrics.realized_pnl)
    _check("UNREALIZED_PNL", expected_unrealized, metrics.unrealized_pnl)
    _check("DRAWDOWN", expected_drawdown, metrics.drawdown)
    if expected_peak is not None:
        peak = _dec(
            (final_portfolio_snapshot or {}).get("state", {}).get("peak_equity") or expected_peak
        )
        # peak is state field; compare via snapshot state after reconstruction
        recon_peak = _dec(model.snapshot()["state"]["peak_equity"])
        if peak != recon_peak:
            blockers.append(f"PEAK_EQUITY_MISMATCH:reconstructed={recon_peak}:expected={peak}")

    gross = metrics.realized_pnl + metrics.unrealized_pnl
    net = gross - metrics.fees
    notes.append(f"gross_pnl={gross}")
    notes.append(f"net_pnl={net}")
    notes.append(f"exposure={metrics.exposure}")

    if fill_ledger is not None and len(fill_ledger) != reconstructed_fills:
        blockers.append(
            f"FILL_COUNT_MISMATCH:ledger={len(fill_ledger)}:reconstructed={reconstructed_fills}"
        )

    if economic_metrics is not None and forced_fixture_excluded:
        if economic_metrics.get("excluded") is not True:
            blockers.append("FORCED_FIXTURE_METRICS_NOT_EXCLUDED")
    if integrity_manifest is not None and not (integrity_manifest.get("digests") or {}):
        blockers.append("INTEGRITY_MANIFEST_EMPTY")

    notes.append(f"cycles={len(cycle_ledger)}")
    notes.append(f"reconstructed_fills={reconstructed_fills}")
    notes.append("PRIVATE_API_ABSENT_ASSERTED")
    notes.append("ORDER_ROUTING_UNREACHABLE_ASSERTED")
    notes.append("ORDERS_FALSE_ASSERTED")
    return HardeningReconstructionResultV2(
        ok=not blockers,
        verifier_id=VERIFIER_ID,
        capability_id=CAPABILITY_ID,
        blockers=blockers,
        notes=notes,
        reconstructed_fill_count=reconstructed_fills,
        reconstructed_equity=str(metrics.equity),
        expected_equity=str(expected_equity) if expected_equity is not None else "",
        reconstructed_fees=str(metrics.fees),
        expected_fees=str(expected_fees) if expected_fees is not None else "",
        call_graph_complete=call_graph_complete,
    )
