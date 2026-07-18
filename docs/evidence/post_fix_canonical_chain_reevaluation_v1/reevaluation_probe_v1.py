#!/usr/bin/env python3
"""READ-ONLY post-fix canonical chain reevaluation probe (evidence-only).

Post PR #5338 (mark-relative BPS) + PR #5340 (ADVERSE_EXIT / DOWNSCOPE dual preserve).
No productive mutation. No orders / live / runtime bridge activation.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
for p in (_REPO, _REPO / "src", _REPO / "src" / "trading"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.backtest.admissible_versioned_futures_dataset_v1 import (  # noqa: E402
    DatasetProfileBindingV1,
    DatasetProfileV1,
    ExecutionCostBindingV1,
    L1ObservationStatusV1,
)
from src.backtest.mv2_research_wiring_v1 import (  # noqa: E402
    compute_mv2_research_scope_distances_absolute_from_mark_v1,
    run_mv2_research_backtest_wiring_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)
from trading.master_v2.canonical_market_context_v1 import (  # noqa: E402
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.canonical_scope_initialization_v1 import (  # noqa: E402
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
    with_computed_semantic_digest,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (  # noqa: E402
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    CanonicalScopeEventType,
    ScopeCandidateKind,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventGeneratorInputV1,
    ScopeEventGeneratorPolicyV1,
    compute_evaluated_thresholds,
    generate_deterministic_scope_event,
)
from trading.master_v2.double_play_state import (  # noqa: E402
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    SideState,
    StaticHardLimits,
    transition_state,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (  # noqa: E402
    _canonical_scope_event_to_scope_event,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (  # noqa: E402
    derive_scope_adverse_exit_signal_v0,
)

EVIDENCE = Path(__file__).resolve().parent
SOURCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)

# Same deterministic 1INCH fixture used for PR #5338 measurement.
PRIMARY_MID = "okx:linear_perpetual:1INCH:USDT:USDT:perp"
MATRIX = [
    ("1INCH", "okx:linear_perpetual:1INCH:USDT:USDT:perp", "low"),
    ("BONK", "okx:linear_perpetual:BONK:USDT:USDT:perp", "ultra_low"),
    ("AVAX", "okx:linear_perpetual:AVAX:USDT:USDT:perp", "mid"),
    ("SOL", "okx:linear_perpetual:SOL:USDT:USDT:perp", "high"),
]

LEGACY_ABS_UP = 120.0


@dataclass
class ProbeAcc:
    event_counts: Counter = field(default_factory=Counter)
    matched_counts: Counter = field(default_factory=Counter)
    mapped_scope_event: Counter = field(default_factory=Counter)
    side_before: Counter = field(default_factory=Counter)
    side_after: Counter = field(default_factory=Counter)
    transition_allowed: Counter = field(default_factory=Counter)
    transition_reason: Counter = field(default_factory=Counter)
    composition_status: Counter = field(default_factory=Counter)
    composition_side: Counter = field(default_factory=Counter)
    decision_outcome: Counter = field(default_factory=Counter)
    entry_exit_outcome: Counter = field(default_factory=Counter)
    exit_class: Counter = field(default_factory=Counter)
    reason_codes: Counter = field(default_factory=Counter)
    order_intent: Counter = field(default_factory=Counter)
    marks_valid: int = 0
    marks_invalid: int = 0
    bars_hooked: int = 0
    bull_candidate: int = 0
    bear_candidate: int = 0
    threshold_miss: int = 0
    adverse_geometry: int = 0
    legacy_abs_seen: int = 0
    scale_invariant_ok: int = 0
    scale_invariant_fail: int = 0
    adverse_policy_triggered: int = 0
    entry_policy_enter: int = 0
    exit_policy_exit: int = 0
    hold_noop_intent: int = 0
    bull_transition: int = 0
    bear_transition: int = 0
    downscope_transition: int = 0
    stay_transition: int = 0
    rejected_transition: int = 0
    entry_side_none: int = 0
    entry_side_other: int = 0
    conflicting_intents: int = 0
    traces: list[dict[str, Any]] = field(default_factory=list)
    bps_samples: list[dict[str, Any]] = field(default_factory=list)
    mark_min: Optional[float] = None
    mark_max: Optional[float] = None
    first_blocking: Optional[dict[str, Any]] = None


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bars_path(member_id: str) -> Path:
    scratch = SOURCE / "scratch"
    primary = scratch / member_id.replace(":", "_") / "bars.parquet"
    if primary.is_file():
        return primary
    alt = scratch / "datasets" / member_id.replace(":", "_") / "bars.parquet"
    if alt.is_file():
        return alt
    raise FileNotFoundError(member_id)


def _profile() -> DatasetProfileBindingV1:
    return DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=5.0,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )


def _enum_val(obj: Any) -> str:
    if obj is None:
        return ""
    return str(getattr(obj, "value", obj))


def _is_bull_side(side: str) -> bool:
    s = side.lower()
    return "long_active" in s or s == "long_armed"


def _is_bear_side(side: str) -> bool:
    s = side.lower()
    return "short" in s


def _is_downscope_event(ev: str) -> bool:
    return "downscope" in ev.lower()


def _is_upscope_event(ev: str) -> bool:
    return "upscope" in ev.lower()


def _probe_member(
    member_id: str, cfg: dict[str, Any], collect_traces: bool = True
) -> dict[str, Any]:
    bars = pd.read_parquet(_bars_path(member_id))
    acc = ProbeAcc()
    prior_mark: Optional[float] = None

    def hook(**kwargs: Any) -> None:
        nonlocal prior_mark
        acc.bars_hooked += 1
        inter = kwargs.get("intermediate")
        material = kwargs.get("agreement_material")
        decision = str(kwargs.get("decision_outcome") or "")
        if decision:
            acc.decision_outcome[decision] += 1

        if material is not None:
            entry_side = _enum_val(getattr(material, "entry_side", None))
            if entry_side == "NONE" or entry_side == "":
                acc.entry_side_none += 1
            else:
                acc.entry_side_other += 1

        if inter is None:
            if acc.first_blocking is None:
                acc.first_blocking = {
                    "boundary": "src/backtest/mv2_research_wiring_v1.py:observational_hook",
                    "symbol": "intermediate_missing",
                    "reason": "no_intermediate",
                }
            prior_mark = None
            return

        se = getattr(inter, "scope_event", None)
        switch = getattr(inter, "state_switch", None)
        composition = getattr(inter, "composition_result", None)
        entry_exit = getattr(inter, "entry_exit_decision", None)
        order_intent = getattr(inter, "canonical_order_intent", None)

        if se is None:
            if acc.first_blocking is None:
                acc.first_blocking = {
                    "boundary": "trading.master_v2.deterministic_scope_event_generator_v1",
                    "symbol": "generate_deterministic_scope_event",
                    "reason": "scope_event_missing",
                }
            return

        event_type = _enum_val(getattr(se, "event_type", None))
        acc.event_counts[event_type] += 1
        matched = tuple(getattr(se, "matched_conditions", ()) or ())
        for m in matched:
            acc.matched_counts[str(m)] += 1

        binding = getattr(se, "semantic_binding", None)
        mark = float(getattr(binding, "current_price", 0.0) or 0.0)
        trailing = float(getattr(binding, "trailing_anchor", 0.0) or 0.0)
        up_d = float(getattr(binding, "up_distance", 0.0) or 0.0)
        adverse_d = float(getattr(binding, "adverse_exit_distance", 0.0) or 0.0)
        reversal_d = float(getattr(binding, "reversal_distance", 0.0) or 0.0)

        if math.isfinite(mark) and mark > 0:
            acc.marks_valid += 1
            if acc.mark_min is None or mark < acc.mark_min:
                acc.mark_min = mark
            if acc.mark_max is None or mark > acc.mark_max:
                acc.mark_max = mark
            helper = compute_mv2_research_scope_distances_absolute_from_mark_v1(mark)
            if (
                math.isclose(helper.up_distance, up_d, rel_tol=0, abs_tol=1e-12)
                and math.isclose(helper.adverse_exit_distance, adverse_d, rel_tol=0, abs_tol=1e-12)
                and math.isclose(helper.reversal_distance, reversal_d, rel_tol=0, abs_tol=1e-12)
            ):
                acc.scale_invariant_ok += 1
            else:
                acc.scale_invariant_fail += 1
            # Scale-invariance: distances / mark ≈ constant BPS ratios
            if mark > 0:
                up_bps = up_d / mark * 10_000.0
                if math.isclose(up_bps, 100.0, rel_tol=0, abs_tol=1e-6):
                    pass
            if math.isclose(up_d, LEGACY_ABS_UP, rel_tol=0, abs_tol=1e-9):
                acc.legacy_abs_seen += 1
            if len(acc.bps_samples) < 8:
                acc.bps_samples.append(
                    {
                        "mark": mark,
                        "up_distance": up_d,
                        "adverse_exit_distance": adverse_d,
                        "reversal_distance": reversal_d,
                        "up_bps": up_d / mark * 10_000.0,
                        "adverse_bps": adverse_d / mark * 10_000.0,
                        "reversal_bps": reversal_d / mark * 10_000.0,
                    }
                )
        else:
            acc.marks_invalid += 1

        thr = compute_evaluated_thresholds(
            direction=ScopeDirectionState.LONG,
            trailing_anchor=trailing,
            up_distance=up_d,
            adverse_exit_distance=adverse_d,
            reversal_distance=reversal_d,
        )
        bull = mark >= thr.up_candidate_threshold
        bear = mark <= thr.downscope_candidate_threshold
        adverse_hit = mark <= thr.adverse_exit_threshold
        if bull:
            acc.bull_candidate += 1
        if bear:
            acc.bear_candidate += 1
        if adverse_hit:
            acc.adverse_geometry += 1
        if not bull and not bear and not adverse_hit:
            acc.threshold_miss += 1

        mapped = _canonical_scope_event_to_scope_event(
            CanonicalScopeEventType(event_type) if event_type else CanonicalScopeEventType.NOOP,
            matched_conditions=matched,
        )
        mapped_name = mapped.value if hasattr(mapped, "value") else str(mapped)
        acc.mapped_scope_event[mapped_name] += 1

        adverse_signal = derive_scope_adverse_exit_signal_v0(se)
        if getattr(adverse_signal, "triggered", False):
            acc.adverse_policy_triggered += 1

        side_before = ""
        side_after = ""
        if switch is not None:
            side_before = str(getattr(switch, "previous_side_state", "") or "")
            side_after = str(getattr(switch, "next_side_state", "") or "")
            allowed = bool(getattr(switch, "transition_allowed", False))
            reason = str(getattr(switch, "transition_reason_code", "") or "")
            acc.side_before[side_before] += 1
            acc.side_after[side_after] += 1
            acc.transition_allowed[str(allowed)] += 1
            acc.transition_reason[reason] += 1
            if side_before == side_after:
                acc.stay_transition += 1
            else:
                if _is_upscope_event(event_type) or (
                    _is_bull_side(side_after) and not _is_bull_side(side_before)
                ):
                    acc.bull_transition += 1
                if _is_bear_side(side_after) and not _is_bear_side(side_before):
                    acc.bear_transition += 1
                if _is_downscope_event(event_type) or _is_downscope_event(mapped_name):
                    acc.downscope_transition += 1
            if not allowed and side_before == side_after:
                acc.rejected_transition += 1

        if composition is not None:
            acc.composition_status[_enum_val(getattr(composition, "composition_status", None))] += 1
            acc.composition_side[_enum_val(getattr(composition, "selected_side", None))] += 1

        ee_outcome = ""
        ee_exit = ""
        ee_reasons: tuple[str, ...] = ()
        if entry_exit is not None:
            ee_outcome = _enum_val(getattr(entry_exit, "decision_outcome", None))
            ee_exit = _enum_val(getattr(entry_exit, "exit_class", None))
            ee_reasons = tuple(getattr(entry_exit, "reason_codes", ()) or ())
            acc.entry_exit_outcome[ee_outcome] += 1
            acc.exit_class[ee_exit] += 1
            for rc in ee_reasons:
                acc.reason_codes[str(rc)] += 1
            if ee_outcome in {"enter_long", "enter_short"}:
                acc.entry_policy_enter += 1
            if ee_outcome == "exit" or ee_exit not in {"", "none", "NONE"}:
                # ExitClass.NONE is "none"
                if ee_outcome == "exit" or (ee_exit and ee_exit.lower() not in {"none", ""}):
                    acc.exit_policy_exit += 1
            if ee_outcome in {"no_action", "observe", "hold"}:
                acc.hold_noop_intent += 1
            if ee_outcome in {"enter_long", "enter_short"} and ee_exit not in {
                "",
                "none",
                "NONE",
            }:
                if ee_exit.lower() not in {"none", ""}:
                    acc.conflicting_intents += 1

        if order_intent is None:
            acc.order_intent["none"] += 1
        else:
            acc.order_intent["present"] += 1

        # First blocking heuristic on strategy ENTRY bars
        raw = int(kwargs.get("raw_strategy_signal", 0) or 0)
        if acc.first_blocking is None and raw == 1:
            if ee_outcome in {"enter_long", "enter_short"}:
                pass
            elif ee_outcome == "no_action" and any(
                "selected_opposite" in r or "direction_not_armed" in r for r in ee_reasons
            ):
                acc.first_blocking = {
                    "boundary": (
                        "trading.master_v2.double_play_entry_exit_policy_v0."
                        "evaluate_double_play_entry_exit_policy_v0"
                    ),
                    "symbol": "evaluate_double_play_entry_exit_policy_v0",
                    "reason": "|".join(ee_reasons) or ee_outcome,
                    "side_after": side_after,
                    "composition_side": _enum_val(getattr(composition, "selected_side", None))
                    if composition
                    else "",
                    "event_type": event_type,
                    "mapped": mapped_name,
                }
            elif decision in {"blocked", "observe"} and ee_outcome not in {
                "enter_long",
                "enter_short",
            }:
                acc.first_blocking = {
                    "boundary": "canonical_chain_entry",
                    "symbol": ee_outcome or decision,
                    "reason": "|".join(ee_reasons) or decision,
                    "side_after": side_after,
                    "event_type": event_type,
                }

        if collect_traces and len(acc.traces) < 40:
            has_adverse = ScopeCandidateKind.ADVERSE_EXIT.value in matched
            has_down = ScopeCandidateKind.DOWNSCOPE.value in matched
            interesting = (
                has_adverse
                or has_down
                or _is_downscope_event(event_type)
                or event_type == "adverse_exit_candidate"
                or side_before != side_after
                or ee_outcome in {"enter_long", "enter_short", "exit"}
            )
            if interesting:
                acc.traces.append(
                    {
                        "instrument": member_id,
                        "timestamp": str(kwargs.get("bar_timestamp")),
                        "epoch": int(kwargs.get("trading_epoch", -1)),
                        "mark": mark,
                        "prior_mark": prior_mark,
                        "up_distance": up_d,
                        "adverse_exit_distance": adverse_d,
                        "reversal_distance": reversal_d,
                        "event_type": event_type,
                        "matched": "|".join(str(x) for x in matched),
                        "mapped_scope_event": mapped_name,
                        "adverse_policy_triggered": bool(
                            getattr(adverse_signal, "triggered", False)
                        ),
                        "adverse_policy_reason": str(
                            getattr(adverse_signal, "reason_code", "") or ""
                        ),
                        "side_before": side_before,
                        "side_after": side_after,
                        "transition_allowed": bool(getattr(switch, "transition_allowed", False))
                        if switch
                        else None,
                        "transition_reason": str(
                            getattr(switch, "transition_reason_code", "") or ""
                        )
                        if switch
                        else "",
                        "composition_side": _enum_val(getattr(composition, "selected_side", None))
                        if composition
                        else "",
                        "entry_exit_outcome": ee_outcome,
                        "exit_class": ee_exit,
                        "reason_codes": "|".join(ee_reasons),
                        "decision_outcome": decision,
                        "order_intent": "present" if order_intent is not None else "none",
                        "bull_geometry": bull,
                        "bear_geometry": bear,
                        "adverse_geometry": adverse_hit,
                    }
                )
        prior_mark = mark

    result = run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=str(cfg["economic_evaluation_v1"]["strategy_id"]),
        cfg=cfg,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=_profile(),
        observational_bar_hook=hook,
        observational_panel_member_instrument_id=member_id,
    )

    trades_df = getattr(result.backtest_result, "trades", None)
    trade_count = 0
    long_trades = 0
    short_trades = 0
    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trade_count = int(len(trades_df))
        side_col = None
        for c in ("side", "position_side", "trade_side", "direction"):
            if c in trades_df.columns:
                side_col = c
                break
        if side_col:
            for v in trades_df[side_col].astype(str).str.lower():
                if "short" in v or v in {"-1", "sell"}:
                    short_trades += 1
                elif "long" in v or v in {"1", "buy"}:
                    long_trades += 1
        stats = getattr(result.backtest_result, "stats", None) or {}
        if isinstance(stats, dict):
            trade_count = max(trade_count, int(stats.get("total_trades", 0) or 0))

    bull_events = int(
        acc.event_counts.get("upscope_candidate", 0) + acc.event_counts.get("upscope_confirmed", 0)
    )
    bear_events = int(
        acc.event_counts.get("downscope_candidate", 0)
        + acc.event_counts.get("downscope_confirmed", 0)
    )
    adverse_events = int(acc.event_counts.get("adverse_exit_candidate", 0))
    downscope_events = bear_events
    scope_unknown_mapped = int(acc.mapped_scope_event.get("scope_unknown", 0))

    return {
        "member_id": member_id,
        "bars_total": int(len(bars)),
        "bars_hooked": acc.bars_hooked,
        "mark_min": acc.mark_min,
        "mark_max": acc.mark_max,
        "marks_valid": acc.marks_valid,
        "marks_invalid": acc.marks_invalid,
        "event_counts": dict(sorted(acc.event_counts.items())),
        "matched_counts": dict(sorted(acc.matched_counts.items())),
        "mapped_scope_event": dict(sorted(acc.mapped_scope_event.items())),
        "noop_count": int(acc.event_counts.get("noop", 0)),
        "threshold_miss_count": acc.threshold_miss,
        "bull_candidate_count": acc.bull_candidate,
        "bear_candidate_count": acc.bear_candidate,
        "adverse_geometry_count": acc.adverse_geometry,
        "bull_event_count": bull_events,
        "bear_event_count": bear_events,
        "adverse_exit_event_count": adverse_events,
        "downscope_event_count": downscope_events,
        "scope_unknown_mapped_count": scope_unknown_mapped,
        "legacy_absolute_distance_seen": acc.legacy_abs_seen,
        "scale_invariant_ok": acc.scale_invariant_ok,
        "scale_invariant_fail": acc.scale_invariant_fail,
        "bps_samples": acc.bps_samples,
        "side_before": dict(sorted(acc.side_before.items())),
        "side_after": dict(sorted(acc.side_after.items())),
        "transition_allowed": dict(sorted(acc.transition_allowed.items())),
        "transition_reason": dict(sorted(acc.transition_reason.items())),
        "bull_transition_count": acc.bull_transition,
        "bear_transition_count": acc.bear_transition,
        "downscope_transition_count": acc.downscope_transition,
        "stay_transition_count": acc.stay_transition,
        "rejected_transition_count": acc.rejected_transition,
        "composition_status": dict(sorted(acc.composition_status.items())),
        "composition_side": dict(sorted(acc.composition_side.items())),
        "decision_outcome": dict(sorted(acc.decision_outcome.items())),
        "entry_exit_outcome": dict(sorted(acc.entry_exit_outcome.items())),
        "exit_class": dict(sorted(acc.exit_class.items())),
        "reason_codes_top": dict(acc.reason_codes.most_common(25)),
        "adverse_policy_triggered_count": acc.adverse_policy_triggered,
        "entry_policy_enter_count": acc.entry_policy_enter,
        "exit_policy_exit_count": acc.exit_policy_exit,
        "hold_noop_intent_count": acc.hold_noop_intent,
        "conflicting_intents": acc.conflicting_intents,
        "entry_side_none": acc.entry_side_none,
        "entry_side_other": acc.entry_side_other,
        "order_intent": dict(sorted(acc.order_intent.items())),
        "trade_count": trade_count,
        "long_trade_count": long_trades,
        "short_trade_count": short_trades,
        "first_blocking": acc.first_blocking,
        "traces": acc.traces,
        "zero_trade": trade_count == 0,
    }


def _synth_scope(trailing_anchor: float = 100.0) -> CanonicalScopeSnapshotV1:
    scope = CanonicalScopeSnapshotV1(
        scope_id="scope-reeval-epoch0",
        instrument_id="inst-eth-usdt-perp",
        initialized_at_trading_epoch=0,
        source_market_context_id="ctx-reeval",
        source_input_digest="a" * 64,
        lifecycle_state=CanonicalScopeLifecycleState.SCOPE_VALID,
        reference_price=trailing_anchor,
        volatility_estimate=0.2,
        initial_volatility_distance=20.0,
        scope_band=50.0,
        neutral_upper_boundary=trailing_anchor + 50.0,
        neutral_lower_boundary=trailing_anchor - 50.0,
        trailing_anchor=trailing_anchor,
        min_scope_band=10.0,
        max_scope_band=200.0,
        policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        semantic_digest="",
        reason_codes=(),
    )
    return with_computed_semantic_digest(scope)


def _synth_generate(
    *,
    current_price: float,
    trailing_anchor: float,
    up_distance: float,
    adverse_exit_distance: float,
    reversal_distance: float,
) -> Any:
    conf = ScopeConfirmationStateV1(
        candidate_kind=None,
        candidate_count=0,
        last_evaluated_trading_epoch=0,
    )
    inp = ScopeEventGeneratorInputV1(
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
        market_context_id="ctx-reeval",
        market_context_digest="b" * 64,
        current_scope=_synth_scope(trailing_anchor),
        current_direction_state=ScopeDirectionState.LONG,
        reference_price=trailing_anchor,
        current_price=current_price,
        trailing_anchor=trailing_anchor,
        up_distance=up_distance,
        adverse_exit_distance=adverse_exit_distance,
        reversal_distance=reversal_distance,
        confirmation_epochs=2,
        confirmation_state=conf,
        cooldown_state=ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        cooldown_remaining_epochs=0,
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        bar_finality_status=BarFinalityStatus.FINALIZED,
        policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    )
    policy = ScopeEventGeneratorPolicyV1(
        hard_max_scope_distance=1000.0,
        hard_max_adverse_distance=500.0,
        hard_max_reversal_distance=800.0,
        policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    )
    return generate_deterministic_scope_event(inp, policy)


def _synthetic_dual_traces() -> list[dict[str, Any]]:
    """Deterministic contract traces for Phase D (generator + map + transition_state)."""
    traces: list[dict[str, Any]] = []

    def _run(
        label: str,
        *,
        current_price: float,
        trailing_anchor: float,
        up: float,
        adverse: float,
        reversal: float,
        side: SideState,
    ) -> dict[str, Any]:
        evidence = _synth_generate(
            current_price=current_price,
            trailing_anchor=trailing_anchor,
            up_distance=up,
            adverse_exit_distance=adverse,
            reversal_distance=reversal,
        )
        event_type = evidence.event_type
        matched = tuple(evidence.matched_conditions)
        mapped = _canonical_scope_event_to_scope_event(event_type, matched_conditions=matched)
        adverse_sig = derive_scope_adverse_exit_signal_v0(evidence)
        st = RuntimeScopeState(
            anchor_price=trailing_anchor,
            current_upscope_boundary=trailing_anchor + up,
            current_downscope_boundary=trailing_anchor - up,
            current_hysteresis_band=max(up * 0.1, 1e-9),
            last_switch_tick=-1_000_000,
            switches_in_window=0,
            window_start_tick=0,
            chop_latched=False,
            now_tick=0,
            last_completed_side_switch_tick=-1_000_000,
            scope_stability_ticks=0,
        )
        next_side, _st2, transition = transition_state(
            side_state=side,
            event=mapped,
            scope_state=st,
            rules=DynamicScopeRules(),
            envelope=RuntimeEnvelope(static=StaticHardLimits(), live_authorization=False),
            now_tick=1,
        )
        return {
            "trace_id": label,
            "source": "synthetic_contract",
            "fixture_id": f"synth|{trailing_anchor}|{current_price}|up={up}|adv={adverse}",
            "input": {
                "current_price": current_price,
                "trailing_anchor": trailing_anchor,
                "up_distance": up,
                "adverse_exit_distance": adverse,
                "reversal_distance": reversal,
                "side_before": side.value,
            },
            "generator_event": event_type.value,
            "matched_conditions": list(matched),
            "policy_signal_adverse_triggered": bool(adverse_sig.triggered),
            "policy_signal_reason": adverse_sig.reason_code,
            "mapped_scope_event": mapped.value,
            "state_before": side.value,
            "state_after": next_side.value,
            "transition_allowed": transition.allowed,
            "transition_reason": transition.reason_code,
            "final_intent": "n/a_unit_trace_no_entry_exit",
            "execution_result": "n/a_unit_trace_offline_only",
        }

    # Distances mirror test_adverse_exit_downscope_priority_v1 (anchor=100).
    cases = [
        (
            "D1_ADVERSE_PLUS_VALID_DOWNSCOPE",
            # adverse=1, up=2 nested; price 97 hits both → DOWNSCOPE + adverse policy
            dict(current_price=97.0, trailing_anchor=100.0, up=2.0, adverse=1.0, reversal=1.5),
        ),
        (
            "D2_ADVERSE_WITHOUT_DOWNSCOPE",
            # price between adverse and downscope → adverse only → SCOPE_UNKNOWN map
            dict(current_price=98.5, trailing_anchor=100.0, up=2.0, adverse=1.0, reversal=1.5),
        ),
        (
            "D3_DOWNSCOPE_WITHOUT_ADVERSE",
            # adverse farther than up; moderate drop hits downscope only
            dict(current_price=97.5, trailing_anchor=100.0, up=2.0, adverse=4.0, reversal=5.0),
        ),
    ]
    for label, kwargs in cases:
        try:
            traces.append(_run(label, side=SideState.LONG_ACTIVE, **kwargs))
        except Exception as exc:  # noqa: BLE001
            traces.append({"trace_id": label, "error": repr(exc)})
    return traces


def _select_live_traces(primary: dict[str, Any]) -> list[dict[str, Any]]:
    """Pick up to three live fixture traces covering Phase D scenarios."""
    traces = list(primary.get("traces") or [])
    selected: list[dict[str, Any]] = []

    def pick(pred, label: str) -> None:
        for t in traces:
            if pred(t):
                out = dict(t)
                out["trace_id"] = label
                out["source"] = "1INCH_fixture"
                selected.append(out)
                return

    pick(
        lambda t: (
            "adverse_exit" in (t.get("matched") or "")
            and "downscope" in (t.get("matched") or "")
            and "downscope" in (t.get("event_type") or "")
        ),
        "D1_ADVERSE_PLUS_VALID_DOWNSCOPE_LIVE",
    )
    pick(
        lambda t: (
            (t.get("event_type") == "adverse_exit_candidate")
            and "downscope" not in (t.get("matched") or "")
            and t.get("adverse_policy_triggered")
        ),
        "D2_ADVERSE_WITHOUT_DOWNSCOPE_LIVE",
    )
    pick(
        lambda t: (
            "downscope" in (t.get("event_type") or "")
            and "adverse_exit" not in (t.get("matched") or "")
            and not t.get("adverse_policy_triggered")
        ),
        "D3_DOWNSCOPE_WITHOUT_ADVERSE_LIVE",
    )
    return selected


def _write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    if not SOURCE.is_dir():
        summary = {"ok": False, "reason": "archive_missing", "source": str(SOURCE)}
        (EVIDENCE / "probe_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(summary, indent=2))
        return 2

    cfg = _load(SOURCE / "runtime_evaluation_config.json")
    matrix_rows: list[dict[str, Any]] = []
    members: dict[str, Any] = {}

    for label, mid, scale in MATRIX:
        print(f"PROBE_START {label} {mid}", flush=True)
        result = _probe_member(mid, cfg, collect_traces=(mid == PRIMARY_MID))
        members[label] = result
        matrix_rows.append(
            {
                "instrument": label,
                "member_id": mid,
                "price_scale": scale,
                "mark_min": result["mark_min"],
                "mark_max": result["mark_max"],
                "bars": result["bars_hooked"],
                "bull_candidates": result["bull_candidate_count"],
                "bear_candidates": result["bear_candidate_count"],
                "bull_events": result["bull_event_count"],
                "bear_events": result["bear_event_count"],
                "downscope_events": result["downscope_event_count"],
                "adverse_exit_events": result["adverse_exit_event_count"],
                "adverse_policy": result["adverse_policy_triggered_count"],
                "long_reachable": int(result["bull_transition_count"] > 0)
                or int(any("long_active" in k for k in (result.get("side_after") or {}))),
                "short_reachable": int(result["bear_transition_count"] > 0)
                or int(any("short" in k for k in (result.get("side_after") or {}))),
                "entry_intents": result["entry_policy_enter_count"],
                "exit_intents": result["exit_policy_exit_count"],
                "trades": result["trade_count"],
                "long_trades": result["long_trade_count"],
                "short_trades": result["short_trade_count"],
                "zero_trade": result["zero_trade"],
                "first_blocking": json.dumps(result.get("first_blocking"), sort_keys=True),
                "noop": result["noop_count"],
                "threshold_miss": result["threshold_miss_count"],
                "legacy_abs_seen": result["legacy_absolute_distance_seen"],
            }
        )
        print(
            json.dumps(
                {
                    "member": label,
                    "noop": result["noop_count"],
                    "bull_c": result["bull_candidate_count"],
                    "bear_c": result["bear_candidate_count"],
                    "bull_e": result["bull_event_count"],
                    "bear_e": result["bear_event_count"],
                    "adverse_e": result["adverse_exit_event_count"],
                    "trades": result["trade_count"],
                    "side_after": result["side_after"],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    primary = members["1INCH"]
    live_traces = _select_live_traces(primary)
    try:
        synth_traces = _synthetic_dual_traces()
    except Exception as exc:  # noqa: BLE001
        synth_traces = [{"trace_id": "SYNTH_ERROR", "error": str(exc)}]

    # Boundary value flow (static map + live counts overlay)
    boundary_rows = [
        {
            "boundary": "strategy_signal",
            "file": "src/strategies/bollinger.py",
            "symbol": "BollingerBandsStrategy.generate_signals",
            "owner_or_consumer": "producer",
            "active_bound": "active",
            "bull_bear_asymmetry": "mean_reversion_short_bias_typical",
            "value_loss_risk": "none_at_this_boundary_post_5337",
            "1inch_note": "signals_non_zero",
        },
        {
            "boundary": "research_wiring",
            "file": "src/backtest/mv2_research_wiring_v1.py",
            "symbol": "_build_replay_input / compute_mv2_research_scope_distances_absolute_from_mark_v1",
            "owner_or_consumer": "owner_distances_consumer_cmc",
            "active_bound": "active",
            "bull_bear_asymmetry": "scale_symmetric_bps",
            "value_loss_risk": "fixed_by_5338_mark_relative_bps",
            "1inch_note": f"legacy_abs_seen={primary['legacy_absolute_distance_seen']}",
        },
        {
            "boundary": "canonical_market_context",
            "file": "src/trading/master_v2/canonical_market_context_v1.py",
            "symbol": "bind_canonical_market_context_event",
            "owner_or_consumer": "owner_cmc",
            "active_bound": "bound",
            "bull_bear_asymmetry": "none",
            "value_loss_risk": "low",
            "1inch_note": f"marks_valid={primary['marks_valid']}",
        },
        {
            "boundary": "DynamicScopeUpdate",
            "file": "src/trading/master_v2/double_play_state.py",
            "symbol": "update_dynamic_boundaries / RuntimeScopeState",
            "owner_or_consumer": "owner_trailing",
            "active_bound": "active",
            "bull_bear_asymmetry": "direction_oriented",
            "value_loss_risk": "low",
            "1inch_note": "trailing_active",
        },
        {
            "boundary": "ScopeEvent",
            "file": "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
            "symbol": "generate_deterministic_scope_event / _select_directional_kind",
            "owner_or_consumer": "owner_scope_event",
            "active_bound": "active",
            "bull_bear_asymmetry": "post_5340_scope_before_exit",
            "value_loss_risk": "shadowing_fixed_by_5340",
            "1inch_note": json.dumps(primary["event_counts"], sort_keys=True),
        },
        {
            "boundary": "transition_state",
            "file": "src/trading/master_v2/double_play_state.py",
            "symbol": "transition_state",
            "owner_or_consumer": "CANONICAL_DIRECTION_OWNER",
            "active_bound": "active",
            "bull_bear_asymmetry": "event_gated",
            "value_loss_risk": "if_mapped_scope_unknown",
            "1inch_note": json.dumps(primary["side_after"], sort_keys=True),
        },
        {
            "boundary": "composition_matrix",
            "file": "src/trading/master_v2/double_play_composition_matrix_v1.py",
            "symbol": "evaluate_double_play_composition_matrix_v1",
            "owner_or_consumer": "CANONICAL_COMPOSITION_OWNER",
            "active_bound": "active",
            "bull_bear_asymmetry": "selects_long_or_short",
            "value_loss_risk": "contractual_block_possible",
            "1inch_note": json.dumps(primary["composition_side"], sort_keys=True),
        },
        {
            "boundary": "policy_entry_exit_intent",
            "file": "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
            "symbol": "evaluate_double_play_entry_exit_policy_v0",
            "owner_or_consumer": "owner_entry_exit",
            "active_bound": "active",
            "bull_bear_asymmetry": "requires_armed_matching_side",
            "value_loss_risk": "selected_opposite_when_side_mismatch",
            "1inch_note": json.dumps(primary["entry_exit_outcome"], sort_keys=True),
        },
        {
            "boundary": "execution_simulation",
            "file": "src/backtest/mv2_research_wiring_v1.py",
            "symbol": "run_mv2_research_backtest_wiring_v1 / offline bar loop",
            "owner_or_consumer": "consumer_offline_execution",
            "active_bound": "active_offline",
            "bull_bear_asymmetry": "maps_enter_long_short",
            "value_loss_risk": "no_intent_no_trade",
            "1inch_note": f"trades={primary['trade_count']}",
        },
        {
            "boundary": "trade_result_ledger",
            "file": "src/backtest/stats.py",
            "symbol": "compute_backtest_stats",
            "owner_or_consumer": "consumer_stats",
            "active_bound": "active",
            "bull_bear_asymmetry": "none",
            "value_loss_risk": "none",
            "1inch_note": f"long={primary['long_trade_count']} short={primary['short_trade_count']}",
        },
    ]

    event_rows = [{"event": k, "count": v} for k, v in primary["event_counts"].items()]
    event_rows.extend(
        [{"event": "MATCHED:" + k, "count": v} for k, v in primary["matched_counts"].items()]
    )
    event_rows.extend(
        [{"event": "MAPPED:" + k, "count": v} for k, v in primary["mapped_scope_event"].items()]
    )

    state_rows = [
        {"metric": "side_before:" + k, "count": v} for k, v in primary["side_before"].items()
    ]
    state_rows.extend(
        {"metric": "side_after:" + k, "count": v} for k, v in primary["side_after"].items()
    )
    state_rows.extend(
        [
            {"metric": "bull_transition_count", "count": primary["bull_transition_count"]},
            {"metric": "bear_transition_count", "count": primary["bear_transition_count"]},
            {
                "metric": "downscope_transition_count",
                "count": primary["downscope_transition_count"],
            },
            {"metric": "stay_transition_count", "count": primary["stay_transition_count"]},
            {
                "metric": "rejected_transition_count",
                "count": primary["rejected_transition_count"],
            },
        ]
    )

    policy_rows = [
        {"metric": "entry_exit:" + k, "count": v} for k, v in primary["entry_exit_outcome"].items()
    ]
    policy_rows.extend(
        {"metric": "exit_class:" + k, "count": v} for k, v in primary["exit_class"].items()
    )
    policy_rows.extend(
        [
            {
                "metric": "adverse_policy_triggered",
                "count": primary["adverse_policy_triggered_count"],
            },
            {
                "metric": "entry_policy_enter",
                "count": primary["entry_policy_enter_count"],
            },
            {"metric": "exit_policy_exit", "count": primary["exit_policy_exit_count"]},
            {"metric": "hold_noop_intent", "count": primary["hold_noop_intent_count"]},
            {"metric": "conflicting_intents", "count": primary["conflicting_intents"]},
            {"metric": "entry_side_none", "count": primary["entry_side_none"]},
            {"metric": "entry_side_other", "count": primary["entry_side_other"]},
        ]
    )

    exec_rows = [
        {"metric": "order_intent:" + k, "count": v} for k, v in primary["order_intent"].items()
    ]
    exec_rows.extend(
        [
            {"metric": "trade_count", "count": primary["trade_count"]},
            {"metric": "long_trade_count", "count": primary["long_trade_count"]},
            {"metric": "short_trade_count", "count": primary["short_trade_count"]},
        ]
    )
    exec_rows.extend(
        {"metric": "decision:" + k, "count": v} for k, v in primary["decision_outcome"].items()
    )

    _write_tsv(EVIDENCE / "boundary_value_flow.tsv", boundary_rows)
    _write_tsv(EVIDENCE / "instrument_matrix.tsv", matrix_rows)
    _write_tsv(EVIDENCE / "event_counts.tsv", event_rows)
    _write_tsv(EVIDENCE / "state_transition_counts.tsv", state_rows)
    _write_tsv(EVIDENCE / "policy_and_intent_counts.tsv", policy_rows)
    _write_tsv(EVIDENCE / "execution_counts.tsv", exec_rows)

    summary = {
        "ok": True,
        "base_sha_expected": "00302a228e47d1cf74e43494a838123d2f803fb8",
        "primary": "1INCH",
        "primary_member_id": PRIMARY_MID,
        "members": {
            k: {kk: vv for kk, vv in v.items() if kk != "traces"} for k, v in members.items()
        },
        "live_traces": live_traces,
        "synthetic_traces": synth_traces,
        "mark_relative_bps_regression_pass": (
            primary["legacy_absolute_distance_seen"] == 0
            and primary["scale_invariant_fail"] == 0
            and primary["bull_candidate_count"] + primary["bear_candidate_count"] > 0
        ),
        "old_absolute_distances_found": primary["legacy_absolute_distance_seen"] > 0,
        "adverse_exit_policy_preserved": primary["adverse_policy_triggered_count"] > 0
        or primary["adverse_exit_event_count"] > 0
        or ScopeCandidateKind.ADVERSE_EXIT.value in (primary.get("matched_counts") or {}),
        "specific_downscope_preserved": primary["downscope_event_count"] > 0,
        "downscope_reaches_transition_state": primary["downscope_transition_count"] > 0
        or any("downscope" in k for k in (primary.get("mapped_scope_event") or {})),
        "side_state_transition_reachable": (
            primary["bull_transition_count"] + primary["bear_transition_count"] > 0
        )
        or len(primary.get("side_after") or {}) > 1,
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
        "live_authorized": False,
        "orders": False,
    }
    (EVIDENCE / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (EVIDENCE / "live_and_synthetic_traces.json").write_text(
        json.dumps(
            {"live": live_traces, "synthetic": synth_traces},
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "summary": str(EVIDENCE / "probe_summary.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
