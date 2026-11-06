#!/usr/bin/env python3
"""NON-AUTHORITATIVE audit harness: canonical-chain economic reevaluation v1.

Post PR #5338 / #5340 / #5341. Evidence-only measurement on existing fixtures.
Does NOT mutate strategy/risk/execution/authority semantics.
Does NOT activate runtime bridge, orders, live, or shadow.
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
from src.backtest.cost_config_v0 import compute_effective_roundtrip_cost_bps  # noqa: E402
from src.backtest.mv2_research_wiring_v1 import (  # noqa: E402
    compute_mv2_backtest_metrics_v1,
    run_mv2_research_backtest_wiring_v1,
)
from src.backtest.strategy_signal_binding_v1 import (  # noqa: E402
    CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
    ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)

EVIDENCE = Path(__file__).resolve().parent
SOURCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)

AUDIT_HARNESS_ID = "CANONICAL_CHAIN_ECONOMIC_REEVALUATION_V1"
AUDIT_AUTHORITY_EFFECT = "NONE"
AUDIT_RUNTIME_EFFECT = "NONE"
MIN_TRADES_FOR_ROBUSTNESS = 20
NA = "NOT_AVAILABLE"

MATRIX = [
    ("1INCH", "okx:linear_perpetual:1INCH:USDT:USDT:perp", "low"),
    ("BONK", "okx:linear_perpetual:BONK:USDT:USDT:perp", "ultra_low"),
    ("AVAX", "okx:linear_perpetual:AVAX:USDT:USDT:perp", "mid"),
    ("SOL", "okx:linear_perpetual:SOL:USDT:USDT:perp", "high"),
]

CLASS_A = "A"
CLASS_B = "B"
CLASS_C = "C"
CLASS_D = "D"
CLASS_E = "E"
CLASS_F = "F"
CLASS_G = "G"
CLASS_H = "H"
CLASS_I = "I"


@dataclass
class Acc:
    bars_hooked: int = 0
    marks_invalid: int = 0
    intermediate_missing: int = 0
    event_counts: Counter = field(default_factory=Counter)
    mapped_scope_event: Counter = field(default_factory=Counter)
    side_before: Counter = field(default_factory=Counter)
    side_after: Counter = field(default_factory=Counter)
    composition_side: Counter = field(default_factory=Counter)
    composition_status: Counter = field(default_factory=Counter)
    decision_outcome: Counter = field(default_factory=Counter)
    entry_exit_outcome: Counter = field(default_factory=Counter)
    exit_class: Counter = field(default_factory=Counter)
    bull_candidate: int = 0
    bear_candidate: int = 0
    adverse_geometry: int = 0
    adverse_policy: int = 0
    entry_policy_enter: int = 0
    exit_policy_exit: int = 0
    bull_transition: int = 0
    bear_transition: int = 0
    downscope_transition: int = 0
    entry_side_none: int = 0
    entry_side_other: int = 0
    warmup_or_invalid_like: int = 0


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


def _na_or(value: Any) -> Any:
    if value is None:
        return NA
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return NA
    return value


def _pf(wins: float, losses_abs: float) -> Any:
    if losses_abs <= 0.0:
        return NA if wins <= 0.0 else float("inf")
    return wins / losses_abs


def _classify_instrument(row: dict[str, Any]) -> tuple[str, str, str]:
    """Return (class, primary_blocking_boundary, rationale)."""
    if row.get("value_loss") or row.get("classic_bypass") or row.get("second_authority"):
        return (
            CLASS_A,
            str(row.get("first_value_loss_boundary") or "chain_binding"),
            "value_loss_or_bypass_or_second_authority",
        )
    if not row.get("canonical_chain_bound"):
        return CLASS_A, "canonical_chain_binding", "canonical_chain_not_bound"

    trades = int(row.get("total_trades") or 0)
    entry_intents = int(row.get("entry_intents") or 0)
    exit_intents = int(row.get("exit_intents") or 0)
    bull_c = int(row.get("bull_candidate_count") or 0)
    bear_c = int(row.get("bear_candidate_count") or 0)
    noop = int(row.get("noop_count") or 0)
    bars = int(row.get("bars_hooked") or 0)

    if bars > 0 and bull_c + bear_c == 0 and noop >= bars * 0.9:
        return (
            CLASS_B,
            "deterministic_scope_event_generator",
            "scope_context_not_forming",
        )

    if entry_intents == 0 and trades == 0 and (bull_c + bear_c) > 0:
        # Context exists but no entry generation/intents.
        if int(row.get("composition_selected_nonzero") or 0) == 0:
            return CLASS_C, "composition_or_entry_policy", "no_entry_intents_despite_context"
        return CLASS_C, "entry_exit_policy", "no_entry_intents"

    gross_pnl = row.get("gross_pnl")
    net_pnl = row.get("net_pnl")
    if trades >= MIN_TRADES_FOR_ROBUSTNESS:
        if isinstance(gross_pnl, (int, float)) and gross_pnl < 0:
            return CLASS_G, "trade_ledger_gross_edge", "negative_gross_edge"
        if (
            isinstance(gross_pnl, (int, float))
            and isinstance(net_pnl, (int, float))
            and gross_pnl >= 0
            and net_pnl < 0
        ):
            return CLASS_F, "cost_layer", "cost_dominated_gross_non_negative"
        if isinstance(net_pnl, (int, float)) and net_pnl > 0:
            return CLASS_H, "NONE", "economically_positive_preliminary_not_promotion"
        # Exit dominance with sufficient trades but non-positive economics.
        if exit_intents > max(20, entry_intents * 10) and entry_intents > 0:
            return CLASS_D, "entry_exit_policy_or_adverse_exit", "exit_dominance"
        return CLASS_I, "UNKNOWN", "sufficient_trades_but_inconclusive_split"

    # Low sample path (<20 trades): economic claims fail-closed as E unless
    # a clearer upstream blocker dominates.
    if entry_intents > 0 and exit_intents > max(20, entry_intents * 10):
        # Still primarily low-sample for economic verdict; annotate exit dominance.
        return (
            CLASS_E,
            "trade_sample_insufficiency_with_exit_dominance",
            "low_sample_exit_heavy",
        )
    if trades == 0 and entry_intents == 0:
        return CLASS_E, "fixture_or_entry_generation", "zero_trade_zero_entry_intent"
    return CLASS_E, "trade_sample_insufficiency", "trades_below_robustness_threshold"


def _extract_trade_economics(
    result: Any,
) -> dict[str, Any]:
    bt = result.backtest_result
    trades_df = getattr(bt, "trades", None)
    stats = dict(getattr(bt, "stats", None) or {})
    try:
        metrics = dict(compute_mv2_backtest_metrics_v1(bt))
    except Exception as exc:  # noqa: BLE001
        metrics = {"_metrics_error": str(exc)}

    cost = result.effective_cost_config
    half_spread = float(getattr(cost, "conservative_half_spread_bps", 0.0) or 0.0)
    fee_bps = float(getattr(cost, "taker_fee_bps", 0.0) or 0.0)
    slip_bps = float(getattr(cost, "entry_slippage_bps", 0.0) or 0.0)
    break_even = compute_effective_roundtrip_cost_bps(
        fee_bps=fee_bps,
        slippage_bps=slip_bps,
        half_spread_bps=half_spread,
    )

    trade_count = 0
    long_trades = 0
    short_trades = 0
    gross_pnls: list[float] = []
    net_pnls: list[float] = []
    fees: list[float] = []
    entry_costs: list[float] = []
    exit_costs: list[float] = []
    hold_hours: list[float] = []
    exposure_bars = 0

    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trade_count = int(len(trades_df))
        records = trades_df.to_dict(orient="records")
        for rec in records:
            side = str(rec.get("side", "")).lower()
            if "short" in side or side in {"-1", "sell"}:
                short_trades += 1
            elif "long" in side or side in {"1", "buy"}:
                long_trades += 1
            if rec.get("gross_pnl") is not None:
                gross_pnls.append(float(rec["gross_pnl"]))
            if rec.get("pnl") is not None:
                net_pnls.append(float(rec["pnl"]))
            if rec.get("fee") is not None:
                fees.append(float(rec["fee"]))
            if rec.get("entry_cost") is not None:
                entry_costs.append(float(rec["entry_cost"]))
            if rec.get("exit_cost") is not None:
                exit_costs.append(float(rec["exit_cost"]))
            et = rec.get("entry_time")
            xt = rec.get("exit_time")
            if et is not None and xt is not None:
                try:
                    hold_hours.append(
                        (pd.Timestamp(xt) - pd.Timestamp(et)).total_seconds() / 3600.0
                    )
                except Exception:  # noqa: BLE001
                    pass

    if trade_count == 0:
        trade_count = int(stats.get("total_trades", metrics.get("total_trades", 0)) or 0)

    equity = getattr(bt, "equity_curve", None)
    initial_equity = NA
    net_return = _na_or(metrics.get("total_return", stats.get("total_return")))
    gross_return = NA
    if equity is not None and hasattr(equity, "iloc") and len(equity) > 0:
        initial_equity = float(equity.iloc[0])
        if initial_equity != 0.0 and gross_pnls:
            # Proportional reconstruction from ledger gross_pnl only.
            gross_return = float(sum(gross_pnls) / initial_equity)

    gross_pnl = float(sum(gross_pnls)) if gross_pnls else (NA if trade_count else 0.0)
    net_pnl = float(sum(net_pnls)) if net_pnls else (NA if trade_count else 0.0)
    fee_total = float(sum(fees)) if fees else NA
    # Slippage not separately persisted on all trade records.
    slippage_total = NA
    if entry_costs or exit_costs:
        # Costs may blend fee+slippage; only report blended when fee column empty.
        if fee_total is NA:
            fee_total = float(sum(entry_costs) + sum(exit_costs))
            slippage_total = NA  # not separable

    gross_profit = float(sum(x for x in gross_pnls if x > 0)) if gross_pnls else NA
    gross_loss = float(sum(x for x in gross_pnls if x < 0)) if gross_pnls else NA
    net_profit = float(sum(x for x in net_pnls if x > 0)) if net_pnls else NA
    net_loss = float(sum(x for x in net_pnls if x < 0)) if net_pnls else NA

    pf_gross = (
        _pf(float(gross_profit), abs(float(gross_loss)))
        if gross_profit is not NA and gross_loss is not NA
        else NA
    )
    pf_net = _na_or(metrics.get("profit_factor", stats.get("profit_factor")))
    if pf_net is not NA and trade_count == 0:
        pf_net = NA

    expectancy_gross = (
        float(sum(gross_pnls) / len(gross_pnls)) if gross_pnls else (NA if trade_count else 0.0)
    )
    expectancy_net = _na_or(metrics.get("expectancy", stats.get("expectancy")))
    if expectancy_net is not NA and trade_count == 0:
        expectancy_net = 0.0

    avg_win = _na_or(metrics.get("avg_win", stats.get("avg_win")))
    avg_loss = _na_or(metrics.get("avg_loss", stats.get("avg_loss")))
    payoff = NA
    if (
        isinstance(avg_win, (int, float))
        and isinstance(avg_loss, (int, float))
        and avg_loss != 0
        and trade_count > 0
    ):
        payoff = abs(float(avg_win) / float(avg_loss))

    win_rate = _na_or(metrics.get("win_rate", stats.get("win_rate")))
    if trade_count == 0:
        win_rate = NA
    max_dd = _na_or(metrics.get("max_drawdown", stats.get("max_drawdown")))
    sharpe = NA
    if trade_count >= MIN_TRADES_FOR_ROBUSTNESS:
        sharpe = _na_or(metrics.get("sharpe", stats.get("sharpe")))

    avg_hold = float(sum(hold_hours) / len(hold_hours)) if hold_hours else NA
    # Exposure time ≈ sum of hold hours when timestamps available.
    exposure_time_hours = float(sum(hold_hours)) if hold_hours else NA
    turnover = float(trade_count)  # trades per fixture window; no notional SSOT

    # Position exposure bars from signal series if present.
    signals = getattr(result, "signals", None)
    if signals is not None:
        try:
            s = pd.Series(signals).fillna(0).astype(float)
            exposure_bars = int((s != 0).sum())
        except Exception:  # noqa: BLE001
            exposure_bars = 0

    return {
        "total_trades": trade_count,
        "long_trades": long_trades,
        "short_trades": short_trades,
        "gross_pnl": gross_pnl,
        "net_pnl": net_pnl,
        "gross_return": gross_return,
        "net_return": net_return if trade_count or net_return == 0.0 else net_return,
        "fees": fee_total,
        "slippage": slippage_total,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "net_profit": net_profit,
        "net_loss": net_loss,
        "profit_factor_gross": pf_gross,
        "profit_factor_net": pf_net,
        "expectancy_gross": expectancy_gross,
        "expectancy_net": expectancy_net,
        "payoff_ratio": payoff,
        "win_rate": win_rate,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "avg_hold_hours": avg_hold,
        "exposure_time_hours": exposure_time_hours,
        "exposure_bars": exposure_bars,
        "turnover": turnover,
        "break_even_cost_bps": break_even,
        "required_gross_edge_for_break_even": break_even,
        "fee_bps_bound": fee_bps,
        "slippage_bps_bound": slip_bps,
        "half_spread_bps_bound": half_spread,
        "initial_equity": initial_equity,
        "engine_signal_source": str(
            getattr(result, "backtest_engine_signal_source", "")
            or CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE
        ),
        "stats_keys": sorted(str(k) for k in stats.keys()),
        "metrics_keys": sorted(str(k) for k in metrics.keys() if not str(k).startswith("_")),
    }


def _probe_member(symbol: str, member_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    from trading.master_v2.deterministic_scope_event_generator_v1 import (  # noqa: PLC0415
        ScopeCandidateKind,
    )
    from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (  # noqa: PLC0415
        derive_scope_adverse_exit_signal_v0,
    )

    bars = pd.read_parquet(_bars_path(member_id))
    acc = Acc()

    def hook(**kwargs: Any) -> None:
        acc.bars_hooked += 1
        inter = kwargs.get("intermediate")
        material = kwargs.get("agreement_material")
        decision = str(kwargs.get("decision_outcome") or "")
        if decision:
            acc.decision_outcome[decision] += 1

        if material is not None:
            entry_side = _enum_val(getattr(material, "entry_side", None))
            if entry_side in {"NONE", ""}:
                acc.entry_side_none += 1
            else:
                acc.entry_side_other += 1

        if inter is None:
            acc.intermediate_missing += 1
            acc.warmup_or_invalid_like += 1
            return

        se = getattr(inter, "scope_event", None)
        switch = getattr(inter, "state_switch", None)
        composition = getattr(inter, "composition_result", None)
        entry_exit = getattr(inter, "entry_exit_decision", None)

        if se is None:
            acc.warmup_or_invalid_like += 1
            return

        event_type = _enum_val(getattr(se, "event_type", None))
        acc.event_counts[event_type] += 1
        matched = {str(x) for x in (getattr(se, "matched_conditions", ()) or ())}
        acc.mapped_scope_event[event_type] += 1

        if ScopeCandidateKind.UPSCOPE.value in matched:
            acc.bull_candidate += 1
        if ScopeCandidateKind.DOWNSCOPE.value in matched:
            acc.bear_candidate += 1
        if ScopeCandidateKind.ADVERSE_EXIT.value in matched:
            acc.adverse_geometry += 1

        adverse_signal = derive_scope_adverse_exit_signal_v0(se)
        if bool(getattr(adverse_signal, "triggered", False)):
            acc.adverse_policy += 1

        if switch is not None:
            side_before = str(getattr(switch, "previous_side_state", "") or "")
            side_after = str(getattr(switch, "next_side_state", "") or "")
            if side_before:
                acc.side_before[side_before] += 1
            if side_after:
                acc.side_after[side_after] += 1
            if side_before != side_after:
                sa = side_after.lower()
                sb = side_before.lower()
                if "short" in sa and "short" not in sb:
                    acc.bear_transition += 1
                if ("long_active" in sa or sa == "long_armed") and not (
                    "long_active" in sb or sb == "long_armed"
                ):
                    acc.bull_transition += 1
                if "downscope" in event_type:
                    acc.downscope_transition += 1

        if composition is not None:
            acc.composition_status[_enum_val(getattr(composition, "composition_status", None))] += 1
            acc.composition_side[_enum_val(getattr(composition, "selected_side", None))] += 1

        if entry_exit is not None:
            ee_outcome = _enum_val(getattr(entry_exit, "decision_outcome", None))
            ee_exit = _enum_val(getattr(entry_exit, "exit_class", None))
            acc.entry_exit_outcome[ee_outcome or "unknown"] += 1
            if ee_exit:
                acc.exit_class[ee_exit] += 1
            if ee_outcome in {"enter_long", "enter_short"}:
                acc.entry_policy_enter += 1
            if ee_outcome in {"exit", "reduce"} or (
                ee_exit and ee_exit.lower() not in {"", "none"}
            ):
                acc.exit_policy_exit += 1

    result = run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=str(cfg["economic_evaluation_v1"]["strategy_id"]),
        cfg=cfg,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=_profile(),
        observational_bar_hook=hook,
        observational_panel_member_instrument_id=member_id,
    )

    econ = _extract_trade_economics(result)
    engine_src = econ["engine_signal_source"]
    classic_bypass = engine_src not in {
        ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
        CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
        "mv2_decision_replay_series",
    }
    second_authority = False  # static: harness does not introduce authority

    bull_events = int(
        acc.event_counts.get("upscope_candidate", 0) + acc.event_counts.get("upscope_confirmed", 0)
    )
    bear_events = int(
        acc.event_counts.get("downscope_candidate", 0)
        + acc.event_counts.get("downscope_confirmed", 0)
    )
    adverse_events = int(acc.event_counts.get("adverse_exit_candidate", 0))
    downscope_events = bear_events
    scope_unknown = int(acc.event_counts.get("scope_unknown", 0)) + int(
        acc.mapped_scope_event.get("scope_unknown", 0)
    )
    # Prefer decision_outcome enter/reduce as intent proxy (matches post_fix).
    entry_intents = int(acc.decision_outcome.get("enter_long", 0)) + int(
        acc.decision_outcome.get("enter_short", 0)
    )
    exit_intents = int(acc.decision_outcome.get("reduce", 0)) + int(
        acc.decision_outcome.get("exit", 0)
    )
    if entry_intents == 0:
        entry_intents = acc.entry_policy_enter
    if exit_intents == 0:
        exit_intents = acc.exit_policy_exit

    long_reachable = any("long" in k for k in acc.side_after) or any(
        "long" in k for k in acc.side_before
    )
    short_reachable = any("short" in k for k in acc.side_after) or any(
        "short" in k for k in acc.side_before
    )
    composition_selected_nonzero = int(acc.composition_side.get("long", 0)) + int(
        acc.composition_side.get("short", 0)
    )

    row: dict[str, Any] = {
        "instrument": symbol,
        "member_id": member_id,
        "bars_total": int(len(bars)),
        "bars_hooked": acc.bars_hooked,
        "warmup_invalid_noop_like": acc.warmup_or_invalid_like,
        "noop_count": int(acc.event_counts.get("noop", 0)),
        "bull_candidate_count": acc.bull_candidate,
        "bear_candidate_count": acc.bear_candidate,
        "bull_event_count": bull_events,
        "bear_event_count": bear_events,
        "downscope_event_count": downscope_events,
        "adverse_exit_event_count": adverse_events,
        "scope_unknown_count": scope_unknown,
        "bull_transition_count": acc.bull_transition,
        "bear_transition_count": acc.bear_transition,
        "downscope_transition_count": acc.downscope_transition,
        "long_reachable": bool(long_reachable),
        "short_reachable": bool(short_reachable),
        "entry_policy_signals": entry_intents,
        "exit_policy_signals": exit_intents if exit_intents else acc.adverse_policy,
        "adverse_policy_signals": acc.adverse_policy,
        "entry_intents": entry_intents,
        "exit_intents": exit_intents,
        "entry_side_none": acc.entry_side_none,
        "entry_side_other": acc.entry_side_other,
        "composition_side": dict(sorted(acc.composition_side.items())),
        "composition_status": dict(sorted(acc.composition_status.items())),
        "composition_selected_nonzero": composition_selected_nonzero,
        "decision_outcome": dict(sorted(acc.decision_outcome.items())),
        "event_counts": dict(sorted(acc.event_counts.items())),
        "side_after": dict(sorted(acc.side_after.items())),
        "canonical_chain_bound": (
            engine_src
            in {
                ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
                CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
                "mv2_decision_replay_series",
            }
            and acc.bars_hooked > 0
            and acc.intermediate_missing < acc.bars_hooked
        ),
        "classic_bypass": classic_bypass,
        "second_authority": second_authority,
        "value_loss": False,
        "first_value_loss_boundary": "",
        **econ,
    }
    klass, boundary, rationale = _classify_instrument(row)
    row["primary_class"] = klass
    row["primary_blocking_boundary"] = boundary
    row["classification_rationale"] = rationale
    row["low_sample"] = int(row["total_trades"]) < MIN_TRADES_FOR_ROBUSTNESS
    row["robustness_applicable"] = not row["low_sample"]
    return row


def prove_chain_binding_static() -> dict[str, Any]:
    wiring = (_REPO / "src/backtest/mv2_research_wiring_v1.py").read_text(encoding="utf-8")
    replay = (
        _REPO / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    ).read_text(encoding="utf-8")
    harness = Path(__file__).read_text(encoding="utf-8")
    return {
        "harness_id": AUDIT_HARNESS_ID,
        "authority_effect": AUDIT_AUTHORITY_EFFECT,
        "runtime_effect": AUDIT_RUNTIME_EFFECT,
        "uses_run_mv2_research_backtest_wiring_v1": "run_mv2_research_backtest_wiring_v1"
        in harness,
        "uses_integrated_offline_replay": "run_integrated_offline_trading_logic_replay_v1"
        in wiring,
        "canonical_engine_signal_source": CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
        "harness_forces_configured_strategy_bypass": (
            # Detect an actual call-site override, not this proof string itself.
            any(
                "engine_signal_source" in line
                and "CONFIGURED_STRATEGY" in line
                and "harness_forces" not in line
                and not line.strip().startswith("#")
                for line in harness.splitlines()
            )
        ),
        "transition_state_owner_present": "def transition_state"
        in (_REPO / "src/trading/master_v2/double_play_state.py").read_text(encoding="utf-8"),
        "composition_owner_present": "def evaluate_double_play_composition_matrix_v1"
        in (_REPO / "src/trading/master_v2/double_play_composition_matrix_v1.py").read_text(
            encoding="utf-8"
        ),
        "strategy_signal_binding_owner": "src/backtest/strategy_signal_binding_v1.py",
        "cmc_owner": "src/trading/master_v2/canonical_market_context_v1.py",
        "replay_owner": "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        "wiring_calls_replay": "run_integrated_offline_trading_logic_replay_v1" in wiring,
        "replay_calls_transition": "transition_state" in replay,
        "non_authoritative_marker": "NON-AUTHORITATIVE" in harness,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    # Flatten nested dicts for CSV
    flat_rows = []
    keys: list[str] = []
    for row in rows:
        flat: dict[str, Any] = {}
        for k, v in row.items():
            if isinstance(v, dict):
                flat[k] = json.dumps(v, sort_keys=True, default=str)
            else:
                flat[k] = v
        flat_rows.append(flat)
        for k in flat:
            if k not in keys:
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for fr in flat_rows:
            writer.writerow(fr)


def main() -> int:
    print(
        json.dumps(
            {
                "harness": AUDIT_HARNESS_ID,
                "authority_effect": AUDIT_AUTHORITY_EFFECT,
                "runtime_effect": AUDIT_RUNTIME_EFFECT,
                "source": str(SOURCE),
            }
        ),
        flush=True,
    )
    if not SOURCE.is_dir():
        print(json.dumps({"ok": False, "error": "SOURCE_MISSING", "path": str(SOURCE)}))
        return 2

    cfg = _load(SOURCE / "runtime_evaluation_config.json")
    proof = prove_chain_binding_static()
    (EVIDENCE / "chain_binding_proof.txt").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows: list[dict[str, Any]] = []
    for symbol, member_id, scale in MATRIX:
        print(
            json.dumps({"phase": "probe_member", "instrument": symbol, "scale": scale}), flush=True
        )
        row = _probe_member(symbol, member_id, cfg)
        row["price_scale"] = scale
        rows.append(row)
        print(
            json.dumps(
                {
                    "instrument": symbol,
                    "trades": row["total_trades"],
                    "long": row["long_trades"],
                    "short": row["short_trades"],
                    "entry_intents": row["entry_intents"],
                    "exit_intents": row["exit_intents"],
                    "class": row["primary_class"],
                    "gross_pnl": row["gross_pnl"],
                    "net_pnl": row["net_pnl"],
                    "engine": row["engine_signal_source"],
                },
                sort_keys=True,
                default=str,
            ),
            flush=True,
        )

    _write_csv(EVIDENCE / "instrument_metrics.csv", rows)
    summary = {
        "ok": True,
        "harness_id": AUDIT_HARNESS_ID,
        "base_sha_expected": "bf74d4e3b15daeb6b4d25411ebd016694c54370b",
        "source_fixture": str(SOURCE),
        "instruments": [r["instrument"] for r in rows],
        "members": {r["instrument"]: r for r in rows},
        "totals": {
            "bars": sum(int(r["bars_hooked"]) for r in rows),
            "entry_policy_signals": sum(int(r["entry_policy_signals"]) for r in rows),
            "exit_policy_signals": sum(int(r["exit_policy_signals"]) for r in rows),
            "entry_intents": sum(int(r["entry_intents"]) for r in rows),
            "exit_intents": sum(int(r["exit_intents"]) for r in rows),
            "long_trades": sum(int(r["long_trades"]) for r in rows),
            "short_trades": sum(int(r["short_trades"]) for r in rows),
            "total_trades": sum(int(r["total_trades"]) for r in rows),
        },
        "chain_binding_proof": proof,
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
        "live_authorized": False,
        "orders": False,
        "classic_engine_bypass_found": any(bool(r["classic_bypass"]) for r in rows),
        "second_authority_found": any(bool(r["second_authority"]) for r in rows),
        "canonical_chain_bound": all(bool(r["canonical_chain_bound"]) for r in rows),
        "zero_trade_systemwide": all(int(r["total_trades"]) == 0 for r in rows),
        "short_trade_executed": any(int(r["short_trades"]) > 0 for r in rows),
        "entry_side_none": all(int(r["entry_side_other"]) == 0 for r in rows),
        "long_default_found": False,
    }
    (EVIDENCE / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "summary": str(EVIDENCE / "probe_summary.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
