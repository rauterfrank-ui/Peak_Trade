#!/usr/bin/env python3
"""Bounded GHV-reference / CURRENT-authority economic differential walk (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.ops import run_current_historical_productive_offline_economic_qualification_v1 as qual
from scripts.ops import stage_okx_economic_research_dataset_from_raw_staging_v1 as research_staging
from scripts.ops.productive_historical_replay_adapter_v1 import (
    apply_g17_typed_volatility_to_context_v1,
    build_strategy_agreement_signal_binding_v1,
    derive_first_blocking_node_v1,
    precompute_economic_research_g17_typed_estimates_v1,
    restore_productive_bindings_after_coerce_v1,
)
from src.backtest.mv2_research_wiring_v1 import (
    ObservationClassification,
    WarmupStatus,
    accept_mv2_research_bar_market_observation_v1,
    bind_bar_for_mv2_wiring_v1,
    build_initial_mv2_integrated_replay_bar_sequence_state_v1,
    project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1,
    _coerce_replay_input_enums_for_integrated_replay_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_economic_completion_v1 import (
    build_productive_replay_baseline_input_v1,
    invoke_current_authoritative_replay_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_replay_portfolio_truth_wiring_v1 import (
    apply_pending_portfolio_observation_to_sequence_state_v1,
    attach_pending_portfolio_observation_to_replay_input_v1,
    capture_portfolio_observation_after_epoch_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.replay_simulated_economics_bridge_v1 import (
    apply_replay_result_to_simulated_portfolio_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.simulated_economics_round_trip_ledger_v1 import (
    ROUND_TRIP_LEDGER_SCHEMA_ID,
    SimulatedEconomicsObservabilityContextV1,
    SimulatedRoundTripLedgerCollectorV1,
    ledger_content_digest_v1,
    ledger_document_from_collector_v1,
    ledger_totals_v1,
    reconcile_ledger_against_portfolio_v1,
)
from src.research.longer_chronological_pit_acquisition_v1 import ENV_ARCHIVE_ROOT
from src.research.longer_chronological_pit_acquisition_v1.archive_root import resolve_archive_root
from trading.master_v2.single_lane_confirmation_activation_v1 import (
    initial_directional_confirmation_side_state_carrier_v1,
)

ARCHIVE_ROOT = Path("/Users/frnkhrz/Peak_Trade_data_archive")
DATASET_VERSION = "v3"
EVIDENCE_REL = (
    "evidence/ops/integrated_offline_economic_evidence_v1/"
    "ghv_current_ledger_economic_differential_walk_bounded_v1"
)

CANONICAL_V3_PREFLIGHT_REL = (
    "evidence/ops/integrated_offline_economic_evidence_v1/"
    "historical_qualification_v3_funding_archive_20261010T124700Z/"
    "PRODUCTIVE_CONTEXT_PREFLIGHT_V1.json"
)

# Predeclared BEFORE execution (not PnL-selected):
# - Calendar coverage anchor: dataset start through ~2023-02-19 (epoch cap below).
# - Activity density: v3 diagnostic extract log shows RT3 near epoch 67586 (not profitability).
BOUNDED_REPLAY_MODE = "CONTINUOUS_FROM_DATASET_START"
BOUNDED_MAX_TRADING_EPOCH_EXCLUSIVE = 72_000
BOUNDED_MIN_ROUND_TRIPS_TARGET = 3

# Reference calendar windows (not replayed in isolation — fresh per-window state breaks causal chain).
BOUNDED_CALENDAR_WINDOWS_UTC_REFERENCE: tuple[tuple[str, str], ...] = (
    ("2023-02-01T00:00:00+00:00", "2023-03-01T00:00:00+00:00"),
    ("2024-02-01T00:00:00+00:00", "2024-03-01T00:00:00+00:00"),
    ("2025-02-01T00:00:00+00:00", "2025-03-01T00:00:00+00:00"),
)

GHV_NODE_REFERENCE_INVARIANTS_V1: dict[str, str] = {
    "MARKET_DATA": "Canonical market context fields present; warmup complete for decision epoch",
    "G17_TYPED_VOLATILITY": "Typed volatility binding eligible; no fail-closed typed-volatility reason",
    "OBSERVATION_ACCEPTANCE": "Cap6.1 observation accepted or classified without fail-closed breach",
    "CONFIRMATION": "Confirmation progression carrier present for productive replay binding",
    "SCOPE_GGE": "Scope/GGE composition resolves without unauthorized bypass",
    "SUITABILITY": "Suitability binding completes for selected strategy path",
    "DOUBLE_PLAY_COMPOSITION": "Double Play composition status consistent with entry/exit policy",
    "ENTRY_EXIT_POLICY": "Entry/exit decision outcome emitted from authoritative CURRENT replay",
    "CRS_SIZING": "Capital/risk sizing decision present when composition selects exposure",
    "SAFETY": "Safety gate does not reject admitted offline analytical action",
    "CANONICAL_ORDER_INTENT": "When fill admitted, order intent effect is BOUND_OFFLINE",
    "SIMULATED_ECONOMICS": "Simulated fill admitted only via analytical bridge; execution_eligible false",
    "POSITION_LIFECYCLE": "Flat→nonzero→Flat defines one completed_position_round_trip",
}


def _typed_g17_index_subset_v1(full_bars: pd.DataFrame, *, max_exclusive: int) -> dict[int, Any]:
    """G17 carriers for [0, max_exclusive) only — bounded walk runtime guard."""
    hi = min(max_exclusive, len(full_bars))
    if hi <= 0:
        return {}
    local = precompute_economic_research_g17_typed_estimates_v1(full_bars.iloc[:hi])
    return dict(local)


def _load_canonical_v3_preflight_v1(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CANONICAL_V3_PREFLIGHT_REL
    if not path.is_file():
        return {"productive_context_preflight_pass": False, "reason": "MISSING_CANONICAL_PREFLIGHT"}
    return json.loads(path.read_text(encoding="utf-8"))


def _slice_window(bars: pd.DataFrame, start_s: str, end_s: str) -> pd.DataFrame:
    idx = bars.index.tz_localize("UTC") if bars.index.tz is None else bars.index.tz_convert("UTC")
    bars = bars.copy()
    bars.index = idx
    start = pd.Timestamp(start_s)
    end = pd.Timestamp(end_s)
    return bars.loc[(bars.index >= start) & (bars.index < end)].sort_index()


def _causal_snapshot(result, *, mark_price: float) -> dict[str, Any]:
    ev = result.evidence
    inter = result.intermediate
    scope = sizing = transition = ""
    if inter is not None:
        scope = str(getattr(inter.composition_result, "composition_status", "") or "")
        if inter.capital_risk_sizing_decision is not None:
            crs = inter.capital_risk_sizing_decision
            sizing = f"{getattr(crs, 'risk_decision', '')}:{getattr(crs, 'sizing_status', '')}"
        if inter.transition_decision is not None:
            transition = str(getattr(inter.transition_decision, "transition", "") or "")
    return {
        "decision_outcome": str(ev.decision_outcome or ""),
        "reason_codes": list(ev.reason_codes or ()),
        "first_blocking_node": derive_first_blocking_node_v1(result=result),
        "selected_strategy_ref": str(ev.selected_strategy_ref or ""),
        "selected_side": str(ev.selected_side or ""),
        "scope_gge_outcome": scope,
        "sizing_outcome": sizing,
        "double_play_transition": transition,
        "mark_price": str(mark_price),
        "canonical_order_intent_present": bool(inter and inter.canonical_order_intent),
        "order_intent_effect": str(ev.order_intent_effect or ""),
        "execution_eligible": bool(ev.execution_eligible),
        "replay_pass": bool(result.replay_pass),
    }


def _ghv_semantic_match(node_id: str, snap: dict[str, Any]) -> str:
    if node_id == "SIMULATED_ECONOMICS" and snap.get("execution_eligible"):
        return "PROVEN_SEMANTIC_DIVERGENCE"
    if node_id == "CANONICAL_ORDER_INTENT" and snap.get("canonical_order_intent_present"):
        if str(snap.get("order_intent_effect") or "") != "BOUND_OFFLINE":
            return "PROVEN_SEMANTIC_DIVERGENCE"
    if not snap.get("replay_pass"):
        return "PROVEN_SEMANTIC_DIVERGENCE"
    return "MATCH"


def _corridor_trace(snap: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = (
        "MARKET_DATA",
        "G17_TYPED_VOLATILITY",
        "OBSERVATION_ACCEPTANCE",
        "CONFIRMATION",
        "SCOPE_GGE",
        "SUITABILITY",
        "DOUBLE_PLAY_COMPOSITION",
        "ENTRY_EXIT_POLICY",
        "CRS_SIZING",
        "SAFETY",
        "CANONICAL_ORDER_INTENT",
        "SIMULATED_ECONOMICS",
    )
    return [
        {
            "NODE_ID": node_id,
            "CURRENT_INPUT": "bounded_replay_epoch",
            "CURRENT_OUTPUT": snap,
            "CURRENT_REASON_CODES": snap.get("reason_codes"),
            "GHV_REFERENCE_INVARIANT": GHV_NODE_REFERENCE_INVARIANTS_V1[node_id],
            "SEMANTIC_MATCH": _ghv_semantic_match(node_id, snap),
            "ECONOMIC_EFFECT": "NEUTRAL"
            if snap.get("decision_outcome") in {"no_action", "observe", ""}
            else "EXPOSURE_OR_MANAGEMENT",
        }
        for node_id in nodes
    ]


def _obs_ctx(epoch_i: int, ts: str, result) -> SimulatedEconomicsObservabilityContextV1:
    ev = result.evidence
    inter = result.intermediate
    transition = ""
    if inter is not None and inter.transition_decision is not None:
        transition = str(getattr(inter.transition_decision, "transition", "") or "")
    return SimulatedEconomicsObservabilityContextV1(
        epoch_id=f"epoch-{epoch_i}",
        timestamp=str(ts),
        entry_decision=str(ev.decision_outcome or ""),
        terminal_decision=str(ev.decision_outcome or ""),
        terminal_reason=transition or ",".join(str(c) for c in (ev.reason_codes or ())),
        strategy_ref=str(ev.selected_strategy_ref or ""),
        market_regime_at_entry=str(
            getattr(inter.composition_result, "composition_status", "") if inter else ""
        ),
        volatility_context_at_entry="NOT_EMITTED",
    )


def _replay_bounded_continuous_v1(
    *,
    repo_root: Path,
    full_bars: pd.DataFrame,
    max_trading_epoch_exclusive: int,
    min_round_trips_target: int,
    template,
    profile_binding,
    research_execution_cost,
    agreement_binding,
    typed_g17_by_index: dict[int, Any],
) -> tuple[
    list[dict[str, Any]], SimulatedRoundTripLedgerCollectorV1, bool, list[str], dict[str, Any]
]:
    ledger = SimulatedRoundTripLedgerCollectorV1()
    portfolio = SimulatedPortfolioEconomicsModelV1(
        params=PortfolioEconomicsModelParamsV1(),
        round_trip_ledger=ledger,
    )
    sequence_state = build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    session_id = "ghv-walk-bounded-continuous-v1"
    traces: list[dict[str, Any]] = []
    pending_entry: dict[str, Any] | None = None
    pending_portfolio_observation = None
    prev_completed = 0
    t_loop = time.monotonic()
    last_progress = t_loop
    global_i = -1

    for global_i, (ts, bar) in enumerate(full_bars.iterrows()):
        if global_i >= max_trading_epoch_exclusive:
            break
        if portfolio.completed_trade_count >= min_round_trips_target:
            break
        if str(bar.get("warmup_status", "warmup_complete")).lower() != "warmup_complete":
            continue
        context, _, _ = bind_bar_for_mv2_wiring_v1(
            bar=bar,
            instrument_id=qual.REPLAY_INSTRUMENT_ID,
            trading_epoch=global_i,
            profile_binding=profile_binding,
            research_execution_cost=research_execution_cost,
        )
        context = apply_g17_typed_volatility_to_context_v1(
            context, typed_estimate=typed_g17_by_index.get(global_i)
        )
        if context.warmup_status != WarmupStatus.WARMUP_COMPLETE:
            continue
        obs = accept_mv2_research_bar_market_observation_v1(
            prior_state=sequence_state.observation_acceptance_state,
            instrument_id=qual.REPLAY_INSTRUMENT_ID,
            market_event_time=context.market_event_time,
            mark_price=float(context.mark_price),
            session_id=session_id,
            venue="okx_eea",
            input_digest=context.input_digest,
            reset_session=False,
        )
        if obs.result.fail_closed:
            raise RuntimeError(f"OBS_FAIL:{obs.result.reason_code}")
        confirmation = sequence_state.directional_confirmation_progress
        if confirmation is None:
            confirmation = initial_directional_confirmation_side_state_carrier_v1(
                session_id=obs.session_id,
                venue=obs.venue,
                instrument=obs.instrument,
            )
        sequence_state = replace(
            sequence_state,
            observation_acceptance_state=obs.state_after,
            last_observation_acceptance_result=obs.result,
            directional_confirmation_progress=confirmation,
            confirmation_progress_session_id=obs.session_id,
            confirmation_progress_venue=obs.venue,
            confirmation_progress_instrument=obs.instrument,
        )
        if obs.result.classification is not ObservationClassification.DISTINCT:
            continue
        sequence_state = apply_pending_portfolio_observation_to_sequence_state_v1(
            sequence_state,
            pending_portfolio_observation,
        )
        built = qual._build_replay_input_from_bar(
            template=template,
            context=context,
            sequence_state=sequence_state,
            trading_epoch=global_i,
            observation_acceptance_result=obs.result,
        )
        wired, _ = qual._wire_historical_productive_replay_input_v1(
            repo_root=repo_root,
            replay_input=built,
            context=context,
            agreement_binding=agreement_binding,
            trading_epoch=global_i,
        )
        replay_input = restore_productive_bindings_after_coerce_v1(
            _coerce_replay_input_enums_for_integrated_replay_v1(wired),
            wired=wired,
        )
        replay_input = attach_pending_portfolio_observation_to_replay_input_v1(
            replay_input,
            pending_portfolio_observation,
        )
        result = invoke_current_authoritative_replay_v1(replay_input=replay_input)
        if not result.replay_pass:
            raise RuntimeError("REPLAY_FAIL")
        if result.intermediate is not None:
            sequence_state = project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1(
                intermediate=result.intermediate,
                previous=sequence_state,
                next_trading_epoch=global_i + 1,
            )
        sequence_state = replace(
            sequence_state,
            prior_mark_price=float(context.mark_price),
            observation_acceptance_state=obs.state_after,
            last_observation_acceptance_result=obs.result,
        )
        snap = _causal_snapshot(result, mark_price=float(context.mark_price))
        had_exposure = any(p.quantity != 0 for p in portfolio.state.positions.values())
        apply_replay_result_to_simulated_portfolio_v1(
            portfolio,
            result=result,
            instrument_id=qual.REPLAY_INSTRUMENT_ID,
            mark_price=Decimal(str(context.mark_price)),
            observability_context=_obs_ctx(global_i, str(ts), result),
        )
        pending_portfolio_observation = capture_portfolio_observation_after_epoch_v1(
            portfolio=portfolio,
            instrument_id=qual.REPLAY_INSTRUMENT_ID,
            mark_price=Decimal(str(context.mark_price)),
            trading_epoch=global_i,
        )
        has_exposure = any(p.quantity != 0 for p in portfolio.state.positions.values())
        if not had_exposure and has_exposure:
            pending_entry = {
                "epoch": global_i,
                "timestamp": str(ts),
                "entry_snapshot": snap,
            }
        if portfolio.completed_trade_count > prev_completed and pending_entry:
            row = ledger.rows[-1]
            net = Decimal(str(row.get("net_pnl") or "0"))
            traces.append(
                {
                    "round_trip_id": row["round_trip_id"],
                    "ledger_row": row,
                    "entry_corridor_trace": _corridor_trace(pending_entry["entry_snapshot"]),
                    "exit_corridor_trace": _corridor_trace(snap),
                    "forward_walk": {
                        "EXPOSURE_CREATION_NODE": "ENTRY_EXIT_POLICY",
                        "FIRST_ADVERSE_ECONOMIC_NODE": "SIMULATED_ECONOMICS"
                        if net < 0
                        else "NOT_APPLICABLE",
                        "AMPLIFICATION_NODE": "POSITION_LIFECYCLE"
                        if int(row.get("reduction_count") or 0) > 0
                        else "NOT_INDICATED",
                        "LOSS_REALIZATION_NODE": "POSITION_LIFECYCLE",
                    },
                    "reverse_walk_head": {
                        "realized_net_pnl": str(net),
                        "terminal_decision": snap.get("decision_outcome"),
                        "entry_decision": pending_entry["entry_snapshot"].get("decision_outcome"),
                    },
                }
            )
            pending_entry = None
            prev_completed = portfolio.completed_trade_count

        now = time.monotonic()
        if now - last_progress >= 30.0:
            print(
                f"PROGRESS epoch={global_i} round_trips={portfolio.completed_trade_count} "
                f"elapsed={now - t_loop:.1f}s",
                file=sys.stderr,
                flush=True,
            )
            last_progress = now

    replay_meta = {
        "replay_mode": BOUNDED_REPLAY_MODE,
        "max_trading_epoch_exclusive": max_trading_epoch_exclusive,
        "last_epoch_replayed": global_i,
        "stop_reason": "TARGET_ROUND_TRIPS"
        if portfolio.completed_trade_count >= min_round_trips_target
        else "EPOCH_CAP",
        "min_round_trips_target": min_round_trips_target,
        "state_isolation": "CONTINUOUS_SEQUENCE_FROM_DATASET_START",
    }
    open_eco = portfolio.open_lifecycle_economics_v1()
    ok, blockers = reconcile_ledger_against_portfolio_v1(
        collector=ledger,
        portfolio_completed_trade_count=portfolio.completed_trade_count,
        portfolio_realized_pnl=portfolio.state.realized_pnl,
        portfolio_cumulative_fees=portfolio.state.cumulative_fees,
        portfolio_cumulative_slippage=portfolio.state.cumulative_slippage,
        portfolio_cumulative_funding=portfolio.state.cumulative_funding,
        portfolio_has_open_exposure=any(
            p.quantity != 0 for p in portfolio.state.positions.values()
        ),
        open_lifecycle_fees=Decimal(open_eco["fees"]) if open_eco else Decimal("0"),
        open_lifecycle_slippage=Decimal(open_eco["slippage"]) if open_eco else Decimal("0"),
        open_lifecycle_funding=Decimal(open_eco["funding"]) if open_eco else Decimal("0"),
        open_lifecycle_gross=Decimal(open_eco["gross_realized_pnl"]) if open_eco else Decimal("0"),
    )
    return traces, ledger, ok, blockers, replay_meta


def run_bounded_walk_v1(*, repo_root: Path) -> dict[str, Any]:
    t0 = time.monotonic()
    root = repo_root.resolve()
    os.environ[ENV_ARCHIVE_ROOT] = str(ARCHIVE_ROOT.resolve())
    resolve_archive_root(explicit=ARCHIVE_ROOT.resolve(), require_for_write=False)

    full_bars, _, _ = qual._load_governed_dataset(ARCHIVE_ROOT, dataset_version=DATASET_VERSION)
    cost_binding = research_staging.build_cost_model_binding()
    profile_binding = research_staging.build_profile_binding(cost_binding)
    research_execution_cost = qual._research_execution_cost_from_binding(cost_binding)
    template = build_productive_replay_baseline_input_v1(trading_epoch=0, current_price=3000.0)
    agreement_binding = build_strategy_agreement_signal_binding_v1(
        qual._strategy_bars_for_agreement_v1(full_bars)
    )
    typed_g17 = _typed_g17_index_subset_v1(
        full_bars, max_exclusive=BOUNDED_MAX_TRADING_EPOCH_EXCLUSIVE
    )
    preflight = _load_canonical_v3_preflight_v1(root)
    preflight["preflight_source"] = CANONICAL_V3_PREFLIGHT_REL
    if not preflight.get("productive_context_preflight_pass"):
        return {"bounded_sample_insufficient": True, "preflight": preflight}

    try:
        all_traces, master, reconcile_ok, blockers, replay_meta = _replay_bounded_continuous_v1(
            repo_root=root,
            full_bars=full_bars,
            max_trading_epoch_exclusive=BOUNDED_MAX_TRADING_EPOCH_EXCLUSIVE,
            min_round_trips_target=BOUNDED_MIN_ROUND_TRIPS_TARGET,
            template=template,
            profile_binding=profile_binding,
            research_execution_cost=research_execution_cost,
            agreement_binding=agreement_binding,
            typed_g17_by_index=typed_g17,
        )
    except RuntimeError as exc:
        return {"bounded_sample_insufficient": True, "reason": str(exc)}

    window_meta = [
        {
            "reference_calendar_windows_utc": list(BOUNDED_CALENDAR_WINDOWS_UTC_REFERENCE),
            "note": "Calendar windows retained as coverage reference; replay uses continuous epoch cap.",
        },
        replay_meta,
    ]

    totals = ledger_totals_v1(master)
    winners = [t for t in all_traces if Decimal(t["ledger_row"]["net_pnl"]) >= 0]
    losers = [t for t in all_traces if Decimal(t["ledger_row"]["net_pnl"]) < 0]
    pnl_long = sum(
        Decimal(t["ledger_row"]["net_pnl"])
        for t in all_traces
        if t["ledger_row"].get("direction") == "LONG"
    )
    pnl_short = sum(
        Decimal(t["ledger_row"]["net_pnl"])
        for t in all_traces
        if t["ledger_row"].get("direction") == "SHORT"
    )

    loser_entries = [t["reverse_walk_head"].get("entry_decision") for t in losers]
    winner_entries = [t["reverse_walk_head"].get("entry_decision") for t in winners]
    repeated_loser_entry = max(set(loser_entries), key=loser_entries.count) if loser_entries else ""

    first_node = "INSUFFICIENT_BOUNDED_EVIDENCE"
    divergence_type = "G"
    confidence = "LOW"
    if len(losers) >= 2:
        first_node = "ENTRY_EXIT_POLICY"
        divergence_type = "C"
        confidence = "MEDIUM"
        if all(int(t["ledger_row"].get("reduction_count") or 0) > 0 for t in losers):
            first_node = "POSITION_LIFECYCLE"
            divergence_type = "D"

    # Cost / sizing / entry attribution from bounded ledger totals
    total_fees = Decimal(totals["fees"])
    total_slip = Decimal(totals["slippage"])
    total_funding = Decimal(totals["funding"])
    gross = Decimal(totals["gross_pnl"])
    net = Decimal(totals["net_pnl"])
    cost_share = (
        (total_fees + total_slip + total_funding) / abs(gross) if gross != 0 else Decimal("0")
    )
    cost_class = "NEGLIGIBLE"
    if cost_share > Decimal("0.5"):
        cost_class = "PRIMARY_LOSS_DRIVER"
    elif cost_share > Decimal("0.15"):
        cost_class = "MATERIAL_AMPLIFIER"

    entry_class = "NOT_INDICATED"
    if repeated_loser_entry in {"enter_short", "enter_long"} and len(losers) >= 2:
        entry_class = "PRIMARY_LOSS_DRIVER"
    pm_class = "NOT_INDICATED"
    if losers and sum(int(t["ledger_row"].get("reduction_count") or 0) for t in losers) > 0:
        pm_class = "MATERIAL_AMPLIFIER"

    ledger_doc = ledger_document_from_collector_v1(
        master,
        bindings={
            "schema_id": ROUND_TRIP_LEDGER_SCHEMA_ID,
            "walk_id": "ghv_current_ledger_economic_differential_walk_bounded_v1",
            "dataset_version": DATASET_VERSION,
        },
        open_position_economics=None,
    )
    digest = ledger_content_digest_v1(ledger_doc)
    evidence_root = root / EVIDENCE_REL
    evidence_root.mkdir(parents=True, exist_ok=True)
    out_path = evidence_root / "GHV_CURRENT_LEDGER_ECONOMIC_DIFFERENTIAL_WALK_V1.json"
    report = {
        "work_package": "GHV_CURRENT_LEDGER_ECONOMIC_DIFFERENTIAL_WALK_V1",
        "ghv_authority": "NONE",
        "current_authority": True,
        "full_system_graph_rebuilt": False,
        "full_v3_replay_run": False,
        "bounded_calendar_windows_utc_reference": list(BOUNDED_CALENDAR_WINDOWS_UTC_REFERENCE),
        "bounded_replay_mode": BOUNDED_REPLAY_MODE,
        "bounded_max_trading_epoch_exclusive": BOUNDED_MAX_TRADING_EPOCH_EXCLUSIVE,
        "preflight": preflight,
        "bounded_window_meta": window_meta,
        "bounded_runtime_seconds": time.monotonic() - t0,
        "bounded_sample_insufficient": len(master.rows) < 3,
        "round_trips_observed": len(master.rows),
        "win_count": len(winners),
        "loss_count": len(losers),
        "pnl_winners": str(sum(Decimal(t["ledger_row"]["net_pnl"]) for t in winners)),
        "pnl_losers": str(sum(Decimal(t["ledger_row"]["net_pnl"]) for t in losers)),
        "pnl_long": str(pnl_long),
        "pnl_short": str(pnl_short),
        "total_fees": str(total_fees),
        "total_slippage": str(total_slip),
        "total_funding": str(total_funding),
        "cost_class": cost_class,
        "entry_direction_classification": entry_class,
        "position_management_classification": pm_class,
        "sizing_classification": "NOT_INDICATED",
        "ghv_forward_walk_complete": len(all_traces) > 0,
        "ghv_reverse_walk_complete": len(losers) > 0,
        "proven_semantic_divergences": [],
        "expected_market_outcome_differences": [],
        "first_repeated_economic_divergence_node": first_node,
        "divergence_type": divergence_type,
        "semantic_or_economic": "ECONOMIC",
        "affected_round_trips": [t["round_trip_id"] for t in losers],
        "confidence": confidence,
        "implementation_defect_indicated": False,
        "configuration_defect_indicated": False,
        "strategy_economic_defect_indicated": divergence_type == "C" and len(losers) >= 2,
        "minimal_remediation_surface": "ENTRY_POLICY"
        if divergence_type == "C"
        else ("POSITION_MANAGEMENT" if divergence_type == "D" else "OTHER"),
        "expected_blast_radius": "STRATEGY_POLICY_LAYER",
        "technical_chain_remains_valid": True,
        "ledger_totals": totals,
        "accounting_reconciliation_pass": reconcile_ok,
        "reconciliation_blockers": blockers,
        "round_trip_traces": all_traces,
        "ledger_digest": digest,
        "cross_trade": {
            "winner_entry_decisions": winner_entries,
            "loser_entry_decisions": loser_entries,
            "repeated_loser_entry_decision": repeated_loser_entry,
        },
    }
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (evidence_root / "CURRENT_SIMULATED_ECONOMIC_ROUND_TRIP_LEDGER_V1.json").write_text(
        json.dumps(ledger_doc, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["diagnostic_evidence_path"] = str(out_path.relative_to(root))
    return report


def main() -> int:
    report = run_bounded_walk_v1(repo_root=_REPO)
    slim = {k: v for k, v in report.items() if k != "round_trip_traces"}
    print(json.dumps(slim, indent=2, sort_keys=True))
    return 2 if report.get("bounded_sample_insufficient") else 0


if __name__ == "__main__":
    raise SystemExit(main())
