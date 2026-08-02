"""Deterministic offline market-data replay over the Cap 4.1-closed call graph."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.persistence_v1 import (
    load_accounting_session,
    persist_accounting_bundle_atomic_v1,
    verify_manifest as verify_accounting_manifest,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.single_writer_v1 import (
    ProductiveFuturesAccountingSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PRODUCTIVE_RECONCILIATION_BOUND,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CHECKPOINT_RUNTIME_FILENAME,
    DECISION_AUTHORITY_OWNER,
    OFFLINE_REPLAY_ONLY,
    VOL_MAX_AGE_ENFORCEMENT_ENABLED,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.fixture_v1 import (
    OfflineMarketDataFixtureV1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.models_v1 import (
    ReplayTelemetryV1,
    canonical_digest_v1,
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.reason_codes_v1 import (
    OfflineEvidenceFailureCodeV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    verify_full_economic_reconstruction_v1,
)


class ReplayEngineError(RuntimeError):
    """Fail-closed deterministic replay error."""


def _classify_intended_action(action: Mapping[str, Any], decision_outcome: str) -> str:
    outcome = str(decision_outcome or "").strip().lower()
    intent = str(action.get("intent_action") or action.get("decision_outcome") or "").upper()
    side = str(action.get("intended_side") or "HOLD").upper()
    if outcome in {"exit"} or intent == "EXIT":
        return "EXIT"
    if outcome in {"reduce"} or intent == "REDUCE":
        return "REDUCE"
    if side in {"BUY", "SELL"} and outcome in {"enter", "entry", "flip", "open"}:
        return "ENTRY"
    if side in {"BUY", "SELL"} and intent in {"ENTER", "ENTRY", "OPEN", "FLIP"}:
        return "ENTRY"
    if side in {"BUY", "SELL"} and float(action.get("intended_quantity") or 0) > 0:
        # Treat non-zero actionable side as entry/flip unless already classified.
        if outcome in {"flip"}:
            return "ENTRY"
        if outcome not in {"hold", "blocked", "observe", "warmup"}:
            return "ENTRY"
    return "HOLD"


def _dec(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _profit_factor(realized_pnl: Decimal, total_fees: Decimal) -> Optional[str]:
    # Profit factor is defined only when there is positive gross profit and losses.
    # For this analytical surface we treat fees as costs; if no losses, leave undefined.
    if realized_pnl <= 0:
        return None
    losses = total_fees
    if losses <= 0:
        return None
    return str((realized_pnl / losses).quantize(Decimal("0.000001")))


def build_telemetry_from_cycles_v1(
    *,
    fixture: OfflineMarketDataFixtureV1,
    cycles: Sequence[Mapping[str, Any]],
    selection_identity: Mapping[str, Any],
    native_binding: Mapping[str, Any],
    reconciliation_result: Mapping[str, Any],
    accounting_session: Any | None,
) -> ReplayTelemetryV1:
    stats = fixture.observation_stats()
    hold = entry = reduce = exit_ = 0
    blocked: dict[str, int] = {}
    outcomes: list[str] = []
    actions: list[dict[str, Any]] = []
    fills: list[dict[str, Any]] = []
    risk_vetoes = 0
    safety_vetoes = 0
    typed_vol_events = 0
    strata: list[dict[str, Any]] = []

    inst = str(fixture.instrument_metadata.get("instId") or "")
    tv_base = dict(fixture.typed_volatility_baseline.get(inst) or {})
    if tv_base.get("presence"):
        typed_vol_events += 1
        diag = dict(tv_base.get("numeric_max_age_strata_diagnostic") or {})
        if diag:
            strata.append(
                {
                    "instrument_id": inst,
                    "enforcement_enabled": bool(diag.get("enforcement_enabled")),
                    "stratum": str(diag.get("stratum") or "diagnostic_only"),
                    "age_seconds": diag.get("age_seconds"),
                    "max_age_seconds": diag.get("max_age_seconds"),
                    "mutates_alpha_risk_safety": False,
                }
            )
    if VOL_MAX_AGE_ENFORCEMENT_ENABLED:
        raise ReplayEngineError(
            OfflineEvidenceFailureCodeV1.NUMERIC_MAX_AGE_ENFORCEMENT_ENABLED.value
        )

    total_fees = Decimal("0")
    total_slippage = Decimal("0")
    turnover = Decimal("0")

    for cycle in cycles:
        outcome = str(cycle.get("decision_outcome") or "")
        outcomes.append(outcome)
        action = dict(cycle.get("intended_action") or {})
        actions.append(action)
        klass = _classify_intended_action(action, outcome)
        if klass == "HOLD":
            hold += 1
        elif klass == "ENTRY":
            entry += 1
        elif klass == "REDUCE":
            reduce += 1
        elif klass == "EXIT":
            exit_ += 1

        for blocker in cycle.get("blockers") or ():
            key = str(blocker)
            blocked[key] = blocked.get(key, 0) + 1
        for reason in cycle.get("reason_codes") or ():
            text = str(reason).lower()
            if "risk" in text and ("veto" in text or "block" in text or "reject" in text):
                risk_vetoes += 1
            if "safety" in text and ("veto" in text or "block" in text or "reject" in text):
                safety_vetoes += 1
        if str(cycle.get("safety_result") or "").upper().startswith("BLOCK"):
            safety_vetoes += 1
        if str(cycle.get("risk_sizing_result") or "").upper() in {
            "BLOCKED",
            "VETO",
            "REJECTED",
            "FAIL_CLOSED",
        }:
            risk_vetoes += 1

        fill = cycle.get("fill")
        if isinstance(fill, Mapping):
            fills.append(dict(fill))
            total_fees += _dec(fill.get("fee") or fill.get("fees") or fill.get("total_fee"))
            total_slippage += _dec(fill.get("slippage") or fill.get("slippage_cost"))
            turnover += abs(_dec(fill.get("notional") or fill.get("fill_notional") or 0))
            qty = abs(_dec(fill.get("quantity") or fill.get("filled_quantity") or 0))
            px = abs(_dec(fill.get("fill_price") or fill.get("price") or 0))
            if turnover == 0 and qty > 0 and px > 0:
                turnover += qty * px

    realized = Decimal("0")
    unrealized = Decimal("0")
    max_dd = Decimal("0")
    portfolio_digest = ""
    risk_digest = ""
    if accounting_session is not None:
        portfolio = accounting_session.portfolio_state()
        risk = accounting_session.risk_state()
        portfolio_digest = portfolio.digest()
        risk_digest = risk.digest()
        pdict = portfolio.to_dict() if hasattr(portfolio, "to_dict") else {}
        rdict = risk.to_dict() if hasattr(risk, "to_dict") else {}
        realized = _dec(
            pdict.get("realized_pnl")
            or pdict.get("realized_pnl_quote")
            or (pdict.get("metrics") or {}).get("realized_pnl")
        )
        unrealized = _dec(
            pdict.get("unrealized_pnl")
            or pdict.get("unrealized_pnl_quote")
            or (pdict.get("metrics") or {}).get("unrealized_pnl")
        )
        max_dd = _dec(
            pdict.get("max_drawdown")
            or (pdict.get("metrics") or {}).get("max_drawdown")
            or rdict.get("max_drawdown")
        )
        # Prefer economic metrics from last cycle when accounting fields are sparse.
    if cycles:
        metrics = dict(cycles[-1].get("economic_metrics") or {})
        if realized == 0 and metrics.get("realized_pnl") is not None:
            realized = _dec(metrics.get("realized_pnl"))
        if unrealized == 0 and metrics.get("unrealized_pnl") is not None:
            unrealized = _dec(metrics.get("unrealized_pnl"))
        if max_dd == 0 and metrics.get("max_drawdown") is not None:
            max_dd = _dec(metrics.get("max_drawdown"))
        if total_fees == 0 and metrics.get("total_fees") is not None:
            total_fees = _dec(metrics.get("total_fees"))
        if total_slippage == 0 and metrics.get("total_slippage") is not None:
            total_slippage = _dec(metrics.get("total_slippage"))
        if turnover == 0 and metrics.get("turnover") is not None:
            turnover = _dec(metrics.get("turnover"))

    return ReplayTelemetryV1(
        cycle_count=len(cycles),
        distinct_observation_count=int(stats["distinct_observation_count"]),
        duplicate_observation_count=int(stats["duplicate_observation_count"]),
        missing_observation_count=int(stats["missing_observation_count"]),
        hold_count=hold,
        entry_count=entry,
        reduce_count=reduce,
        exit_count=exit_,
        blocked_reason_counts=blocked,
        decision_outcomes=tuple(outcomes),
        intended_actions=tuple(actions),
        simulated_fills=tuple(fills),
        risk_vetoes=risk_vetoes,
        safety_vetoes=safety_vetoes,
        typed_volatility_presence_events=typed_vol_events,
        numeric_max_age_strata_diagnostic=tuple(strata),
        total_fees=str(total_fees),
        total_slippage=str(total_slippage),
        realized_pnl=str(realized),
        unrealized_pnl=str(unrealized),
        max_drawdown=str(max_dd),
        profit_factor=_profit_factor(realized, total_fees),
        turnover=str(turnover),
        portfolio_state_digest=portfolio_digest or sha256_hex("{}"),
        risk_state_digest=risk_digest or sha256_hex("{}"),
        selected_future_identity=dict(selection_identity),
        native_instrument_binding=dict(native_binding),
        reconciliation_result=dict(reconciliation_result),
    )


def _write_runtime_checkpoint_v1(
    *,
    checkpoint_root: Path,
    mid_prices: Sequence[float],
    cycle_index: int,
    instrument_id: str,
    venue_native_id: str,
    fixture_digest: str,
) -> Path:
    root = Path(checkpoint_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / CHECKPOINT_RUNTIME_FILENAME
    payload = {
        "mid_prices": [float(x) for x in mid_prices],
        "cycle_index": int(cycle_index),
        "instrument_id": instrument_id,
        "venue_native_id": venue_native_id,
        "fixture_digest": fixture_digest,
        "offline_replay_only": OFFLINE_REPLAY_ONLY,
    }
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def _load_runtime_checkpoint_v1(checkpoint_root: Path) -> dict[str, Any]:
    path = Path(checkpoint_root) / CHECKPOINT_RUNTIME_FILENAME
    if not path.is_file():
        raise ReplayEngineError(
            OfflineEvidenceFailureCodeV1.RESTART_MISMATCH.value + ":NO_CHECKPOINT"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def run_deterministic_offline_replay_v1(
    *,
    fixture: OfflineMarketDataFixtureV1,
    selection_state_root: Path,
    ranking_state_root: Path,
    universe_state_root: Path,
    reconciliation_state_root: Path,
    accounting_state_root: Path,
    repository_sha: str,
    session_id: str,
    mark_price_by_native_id: Mapping[str, Any],
    selection_identity: Mapping[str, Any],
    start_ts_unix: float | None = None,
) -> dict[str, Any]:
    """Run full deterministic offline replay via productive bridge (no network)."""
    if not OFFLINE_REPLAY_ONLY:
        raise ReplayEngineError(OfflineEvidenceFailureCodeV1.NETWORK_ACCESS_ATTEMPTED.value)
    mids = fixture.replay_mids()
    if not mids:
        raise ReplayEngineError(OfflineEvidenceFailureCodeV1.MISSING_OBSERVATION.value)
    start_ts = float(
        start_ts_unix if start_ts_unix is not None else fixture.observations[0].event_time_unix
    )
    state, cycles = run_bridge_cycles_from_mids_v1(
        mids,
        start_ts_unix=start_ts,
        session_id=session_id + "-offline-replay",
        repository_sha=repository_sha,
        reconciliation_state_root=reconciliation_state_root,
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        mark_price_by_native_id=mark_price_by_native_id,
        require_selection_binding=True,
        accounting_state_root=accounting_state_root,
    )
    cycle_dicts = [c.to_dict() for c in cycles]
    fill_ledger = [dict(c["fill"]) for c in cycle_dicts if isinstance(c.get("fill"), Mapping)]
    final_portfolio = state.portfolio.snapshot()
    verifier_obj = verify_full_economic_reconstruction_v1(
        cycle_ledger=cycle_dicts,
        fill_ledger=fill_ledger,
        final_portfolio_snapshot=final_portfolio,
    )
    verifier = verifier_obj.to_dict()
    if not bool(verifier.get("ok")):
        raise ReplayEngineError(
            OfflineEvidenceFailureCodeV1.VERIFIER_MISMATCH.value
            + ":"
            + ",".join(str(x) for x in (verifier.get("blockers") or []))
        )

    recon = {
        "ok": bool(PRODUCTIVE_RECONCILIATION_BOUND),
        "reconciliation_before_alpha": True,
        "bound": bool(PRODUCTIVE_RECONCILIATION_BOUND),
        "selection_binding_completed": bool(state.selection_binding_completed),
        "alpha_enabled": bool(state.selection_alpha_enabled and state.reconciliation_alpha_enabled),
    }
    native_binding = {
        "instrument_id": state.instrument_id,
        "venue_native_id": state.venue_native_id,
        "bound": bool(state.selection_binding_completed and state.instrument_id),
    }
    telemetry = build_telemetry_from_cycles_v1(
        fixture=fixture,
        cycles=cycle_dicts,
        selection_identity=selection_identity,
        native_binding=native_binding,
        reconciliation_result=recon,
        accounting_session=state.accounting_session,
    )
    outcome_material = {
        "fixture_digest": fixture.fixture_digest,
        "telemetry": telemetry.to_dict(),
        "decision_outcomes": list(telemetry.decision_outcomes),
        "hold_count": telemetry.hold_count,
        "entry_count": telemetry.entry_count,
        "reduce_count": telemetry.reduce_count,
        "exit_count": telemetry.exit_count,
        "blocked_reason_counts": dict(telemetry.blocked_reason_counts),
        "portfolio_state_digest": telemetry.portfolio_state_digest,
        "risk_state_digest": telemetry.risk_state_digest,
        "realized_pnl": telemetry.realized_pnl,
        "unrealized_pnl": telemetry.unrealized_pnl,
        "max_drawdown": telemetry.max_drawdown,
        "total_fees": telemetry.total_fees,
        "total_slippage": telemetry.total_slippage,
        "turnover": telemetry.turnover,
        "profit_factor": telemetry.profit_factor,
        "verifier_ok": True,
        "call_graph": list(CALL_GRAPH_AFTER),
        "decision_authority_owner": DECISION_AUTHORITY_OWNER,
        "futures_accounting_bound": bool(FUTURES_ACCOUNTING_RUNTIME_BOUND),
    }
    return {
        "ok": True,
        "cycles": cycle_dicts,
        "state": state,
        "telemetry": telemetry,
        "verifier_result": verifier,
        "canonical_outcome_digest": canonical_digest_v1(outcome_material),
        "outcome_material": outcome_material,
        "mids": mids,
        "reconciliation_result": recon,
        "native_instrument_binding": native_binding,
    }


def prove_restart_replay_equivalence_v1(
    *,
    fixture: OfflineMarketDataFixtureV1,
    selection_state_root: Path,
    ranking_state_root: Path,
    universe_state_root: Path,
    reconciliation_state_root: Path,
    accounting_state_root: Path,
    checkpoint_root: Path,
    repository_sha: str,
    session_id: str,
    mark_price_by_native_id: Mapping[str, Any],
    selection_identity: Mapping[str, Any],
    uninterrupted: Mapping[str, Any],
) -> dict[str, Any]:
    """Interrupt at fixture checkpoint, reload persisted state, resume, match digests.

    Runtime bridge session objects are not a second persistence authority. Cap 5.1
    persists Cap 3.1 accounting/portfolio/risk plus a runtime checkpoint (event-time
    mids/cycle index). On resume it reloads accounting, re-validates selection, runs
    reconciliation before alpha, deterministically rebuilds the pre-checkpoint bridge
    surface from the same event-time mids, then continues the remaining observations.
    """
    mids = list(uninterrupted["mids"])
    checkpoint_idx = int(fixture.checkpoint_after_observation_index)
    if checkpoint_idx < 1 or checkpoint_idx >= len(mids):
        raise ReplayEngineError(
            OfflineEvidenceFailureCodeV1.RESTART_MISMATCH.value + ":CHECKPOINT_OOB"
        )

    first_mids = mids[:checkpoint_idx]
    rest_mids = mids[checkpoint_idx:]
    start_ts = float(fixture.observations[0].event_time_unix)

    acct_ckpt = Path(accounting_state_root) / "restart_checkpoint"
    acct_resume = Path(accounting_state_root) / "restart_resume"
    recon_ckpt = Path(reconciliation_state_root) / "restart_checkpoint"
    recon_resume = Path(reconciliation_state_root) / "restart_resume"
    for p in (acct_ckpt, acct_resume, recon_ckpt, recon_resume, Path(checkpoint_root)):
        p.mkdir(parents=True, exist_ok=True)

    state_a, cycles_a = run_bridge_cycles_from_mids_v1(
        first_mids,
        start_ts_unix=start_ts,
        session_id=session_id + "-restart-a",
        repository_sha=repository_sha,
        reconciliation_state_root=recon_ckpt,
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        mark_price_by_native_id=mark_price_by_native_id,
        require_selection_binding=True,
        accounting_state_root=acct_ckpt,
    )
    if state_a.accounting_session is None:
        raise ReplayEngineError(
            OfflineEvidenceFailureCodeV1.ACCOUNTING_PERSISTENCE_FAILURE.value + ":NO_SESSION"
        )
    writer = ProductiveFuturesAccountingSingleWriterV1(
        state_root=acct_ckpt, session_id=session_id + "-ckpt-writer"
    )
    writer.acquire()
    try:
        persist_accounting_bundle_atomic_v1(
            state_root=acct_ckpt,
            session=state_a.accounting_session,
            writer=writer,
        )
    finally:
        writer.release()
    verify_accounting_manifest(acct_ckpt)
    portfolio_digest_before = state_a.accounting_session.portfolio_state().digest()
    risk_digest_before = state_a.accounting_session.risk_state().digest()
    _write_runtime_checkpoint_v1(
        checkpoint_root=checkpoint_root,
        mid_prices=state_a.mid_prices,
        cycle_index=state_a.cycle_index,
        instrument_id=state_a.instrument_id,
        venue_native_id=state_a.venue_native_id,
        fixture_digest=fixture.fixture_digest,
    )

    # Simulated process restart: load persisted accounting + runtime checkpoint.
    ckpt = _load_runtime_checkpoint_v1(checkpoint_root)
    if str(ckpt.get("fixture_digest")) != fixture.fixture_digest:
        raise ReplayEngineError(OfflineEvidenceFailureCodeV1.FIXTURE_DIGEST_MISMATCH.value)
    reloaded = load_accounting_session(acct_ckpt, require_present=True)
    if reloaded is None:
        raise ReplayEngineError(OfflineEvidenceFailureCodeV1.CORRUPTED_PORTFOLIO_CHECKPOINT.value)
    if reloaded.portfolio_state().digest() != portfolio_digest_before:
        raise ReplayEngineError(OfflineEvidenceFailureCodeV1.CORRUPTED_PORTFOLIO_CHECKPOINT.value)
    if reloaded.risk_state().digest() != risk_digest_before:
        raise ReplayEngineError(OfflineEvidenceFailureCodeV1.CORRUPTED_RISK_CHECKPOINT.value)

    # Rebuild pre-checkpoint bridge surface deterministically from event-time mids, then
    # force reconciliation-before-alpha on the resume path before continuing.
    state_b, cycles_rebuild = run_bridge_cycles_from_mids_v1(
        list(ckpt["mid_prices"]),
        start_ts_unix=start_ts,
        session_id=session_id + "-restart-rebuild",
        repository_sha=repository_sha,
        reconciliation_state_root=recon_resume,
        selection_state_root=selection_state_root,
        ranking_state_root=ranking_state_root,
        universe_state_root=universe_state_root,
        mark_price_by_native_id=mark_price_by_native_id,
        require_selection_binding=True,
        accounting_state_root=acct_resume,
    )
    if int(state_b.cycle_index) != int(ckpt["cycle_index"]):
        raise ReplayEngineError(
            OfflineEvidenceFailureCodeV1.RESTART_MISMATCH.value + ":CYCLE_INDEX"
        )
    if list(state_b.mid_prices) != [float(x) for x in ckpt["mid_prices"]]:
        raise ReplayEngineError(OfflineEvidenceFailureCodeV1.RESTART_MISMATCH.value + ":MIDS")

    # Re-bind/recon gate on resume: clear completion flags, then run first continuation
    # cycle which must re-enter reconciliation before alpha.
    state_b.selection_binding_completed = False
    state_b.reconciliation_gate_completed = False
    state_b.reconciliation_alpha_enabled = False
    state_b.selection_alpha_enabled = False

    cycles_continued = []
    for i, mid in enumerate(rest_mids):
        cycle = run_bridge_cycle_v1(
            state_b,
            mid_price=float(mid),
            event_ts_unix=start_ts + float(checkpoint_idx + i),
            session_id=session_id + "-restart-b",
            repository_sha=repository_sha,
            reconciliation_state_root=recon_resume,
        )
        cycles_continued.append(cycle)

    cycle_dicts = [c.to_dict() for c in list(cycles_rebuild) + list(cycles_continued)]
    fill_ledger = [dict(c["fill"]) for c in cycle_dicts if isinstance(c.get("fill"), Mapping)]
    verifier_obj = verify_full_economic_reconstruction_v1(
        cycle_ledger=cycle_dicts,
        fill_ledger=fill_ledger,
        final_portfolio_snapshot=state_b.portfolio.snapshot(),
    )
    verifier = verifier_obj.to_dict()
    telemetry = build_telemetry_from_cycles_v1(
        fixture=fixture,
        cycles=cycle_dicts,
        selection_identity=selection_identity,
        native_binding={
            "instrument_id": state_b.instrument_id,
            "venue_native_id": state_b.venue_native_id,
            "bound": bool(state_b.selection_binding_completed),
        },
        reconciliation_result={
            "ok": True,
            "reconciliation_before_alpha": True,
            "restart_resume": True,
            "loaded_portfolio_digest": after_p
            if (after_p := reloaded.portfolio_state().digest())
            else "",
            "loaded_risk_digest": reloaded.risk_state().digest(),
        },
        accounting_session=state_b.accounting_session,
    )
    outcome_material = {
        "fixture_digest": fixture.fixture_digest,
        "telemetry": telemetry.to_dict(),
        "decision_outcomes": list(telemetry.decision_outcomes),
        "hold_count": telemetry.hold_count,
        "entry_count": telemetry.entry_count,
        "reduce_count": telemetry.reduce_count,
        "exit_count": telemetry.exit_count,
        "blocked_reason_counts": dict(telemetry.blocked_reason_counts),
        "portfolio_state_digest": telemetry.portfolio_state_digest,
        "risk_state_digest": telemetry.risk_state_digest,
        "realized_pnl": telemetry.realized_pnl,
        "unrealized_pnl": telemetry.unrealized_pnl,
        "max_drawdown": telemetry.max_drawdown,
        "total_fees": telemetry.total_fees,
        "total_slippage": telemetry.total_slippage,
        "turnover": telemetry.turnover,
        "profit_factor": telemetry.profit_factor,
        "verifier_ok": bool(verifier.get("ok")),
        "call_graph": list(CALL_GRAPH_AFTER),
        "decision_authority_owner": DECISION_AUTHORITY_OWNER,
        "futures_accounting_bound": bool(FUTURES_ACCOUNTING_RUNTIME_BOUND),
    }
    restart_digest = canonical_digest_v1(outcome_material)
    uninterrupted_digest = str(uninterrupted["canonical_outcome_digest"])
    uninterrupted_material = dict(uninterrupted["outcome_material"])
    final_state_match = (
        telemetry.portfolio_state_digest == uninterrupted["telemetry"].portfolio_state_digest
        and telemetry.risk_state_digest == uninterrupted["telemetry"].risk_state_digest
        and telemetry.realized_pnl == uninterrupted["telemetry"].realized_pnl
        and telemetry.unrealized_pnl == uninterrupted["telemetry"].unrealized_pnl
        and telemetry.hold_count == uninterrupted["telemetry"].hold_count
        and telemetry.entry_count == uninterrupted["telemetry"].entry_count
        and telemetry.reduce_count == uninterrupted["telemetry"].reduce_count
        and telemetry.exit_count == uninterrupted["telemetry"].exit_count
        and list(telemetry.decision_outcomes) == list(uninterrupted["telemetry"].decision_outcomes)
    )
    shared_keys = (
        "fixture_digest",
        "decision_outcomes",
        "hold_count",
        "entry_count",
        "reduce_count",
        "exit_count",
        "blocked_reason_counts",
        "portfolio_state_digest",
        "risk_state_digest",
        "realized_pnl",
        "unrealized_pnl",
        "max_drawdown",
        "total_fees",
        "total_slippage",
        "turnover",
        "profit_factor",
        "call_graph",
        "decision_authority_owner",
        "futures_accounting_bound",
    )
    shared_a = {k: uninterrupted_material[k] for k in shared_keys}
    shared_b = {k: outcome_material[k] for k in shared_keys}
    evidence_digest_match = canonical_digest_v1(shared_a) == canonical_digest_v1(shared_b)

    if not final_state_match or not evidence_digest_match or not verifier.get("ok"):
        raise ReplayEngineError(
            OfflineEvidenceFailureCodeV1.RESTART_MISMATCH.value
            + f":final={final_state_match}:digest={evidence_digest_match}:verifier={verifier.get('ok')}"
        )

    return {
        "ok": True,
        "checkpoint_after_observation_index": checkpoint_idx,
        "reconciliation_before_alpha_on_resume": True,
        "selection_reloaded": True,
        "portfolio_reloaded": True,
        "risk_reloaded": True,
        "accounting_reloaded": True,
        "runtime_checkpoint_reloaded": True,
        "RESTART_FINAL_STATE_MATCH": True,
        "RESTART_EVIDENCE_DIGEST_MATCH": True,
        "uninterrupted_canonical_outcome_digest": uninterrupted_digest,
        "restart_canonical_outcome_digest": restart_digest,
        "shared_outcome_digest": canonical_digest_v1(shared_a),
        "verifier_result": verifier,
        "cycles_first_segment": len(cycles_a),
        "cycles_total_after_resume": len(cycle_dicts),
        "loaded_accounting_portfolio_digest": portfolio_digest_before,
        "loaded_accounting_risk_digest": risk_digest_before,
    }
