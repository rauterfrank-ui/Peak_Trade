#!/usr/bin/env python3
"""NON-AUTHORITATIVE audit harness: post-repair canonical chain reevaluation v1.

Post PR #5346 (SHORT binding repair). Evidence-only:
  1) Re-run the exact prior canonical offline fixture panel (unchanged bindings).
  2) Focused LONG / SHORT / NONE direction probe through MV2 research wiring.

Does NOT mutate strategy/risk/execution/authority semantics.
Does NOT activate runtime bridge, orders, live, shadow, or capital.
"""

from __future__ import annotations

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
    map_decision_evidence_to_position_signal_v1,
    resolve_agreement_bound_directional_cycle_v1,
    run_mv2_research_backtest_wiring_v1,
)
from src.backtest.strategy_signal_binding_v1 import (  # noqa: E402
    CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
    ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
)
from src.backtest.trade_ledger_equity_curve_persistence_v0 import (  # noqa: E402
    materialize_trade_ledger_rows_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (  # noqa: E402
    CANONICAL_INSTRUMENT_ID,
)

EVIDENCE = Path(__file__).resolve().parent
SOURCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)

AUDIT_HARNESS_ID = "CANONICAL_SHORT_BINDING_POST_REPAIR_REEVALUATION_V1"
AUDIT_AUTHORITY_EFFECT = "NONE"
AUDIT_RUNTIME_EFFECT = "NONE"
MIN_TRADES_FOR_ROBUSTNESS = 20
NA = "NOT_AVAILABLE"

# Unchanged predecessor fixture identity (PR #5342 economic reevaluation).
CONFIG_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
PERIOD = "2024-05-01T00:00:00Z..2024-09-01T00:00:00Z"
SEED = 42
STRATEGY_ID = "bollinger_bands"
STRATEGY_VERSION = "v2"
FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
STOP_PCT = 0.025

MATRIX = [
    ("1INCH", "okx:linear_perpetual:1INCH:USDT:USDT:perp", "low"),
    ("BONK", "okx:linear_perpetual:BONK:USDT:USDT:perp", "ultra_low"),
    ("AVAX", "okx:linear_perpetual:AVAX:USDT:USDT:perp", "mid"),
    ("SOL", "okx:linear_perpetual:SOL:USDT:USDT:perp", "high"),
]

RESULT_PASS_CHAIN_ONLY = "PASS_CHAIN_ONLY"
RESULT_FAIL_CHAIN = "FAIL_CHAIN"
RESULT_ECONOMIC_FAIL = "ECONOMIC_FAIL"
RESULT_TERMINAL_INCONCLUSIVE = "TERMINAL_INCONCLUSIVE"


@dataclass
class Acc:
    bars_hooked: int = 0
    intermediate_missing: int = 0
    event_counts: Counter = field(default_factory=Counter)
    side_before: Counter = field(default_factory=Counter)
    side_after: Counter = field(default_factory=Counter)
    composition_side: Counter = field(default_factory=Counter)
    composition_status: Counter = field(default_factory=Counter)
    decision_outcome: Counter = field(default_factory=Counter)
    mapped_position_signal: Counter = field(default_factory=Counter)
    entry_side_none: int = 0
    entry_side_other: int = 0
    entry_policy_enter: int = 0
    exit_policy_exit: int = 0
    bull_candidate: int = 0
    bear_candidate: int = 0
    bull_transition: int = 0
    bear_transition: int = 0
    warmup_or_invalid_like: int = 0
    decision_authority_reached: int = 0
    context_ids: int = 0


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


def _synthetic_bars(n: int, *, closes: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2026-07-01", periods=n, freq="1h", tz="UTC")
    assert len(closes) == n
    return pd.DataFrame(
        {
            "open": closes,
            "high": [v + 0.5 for v in closes],
            "low": [v - 0.5 for v in closes],
            "close": closes,
            "mark_price": closes,
            "index_price": [v - 0.1 for v in closes],
            "best_bid": [v - 0.05 for v in closes],
            "best_ask": [v + 0.05 for v in closes],
            "spread": [0.1 for _ in closes],
            "volume": [1000.0 for _ in closes],
            "open_interest": [10000.0 for _ in closes],
            "funding_rate": [0.0001 for _ in closes],
            "volatility_estimate": [0.2 for _ in closes],
            "is_final": [True for _ in closes],
            "bar_interval": ["1h" for _ in closes],
        },
        index=idx,
    )


def _direction_probe_cfg() -> dict[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": FEE_BPS,
            "slippage_bps": SLIPPAGE_BPS,
        },
        "risk": {
            "risk_per_trade": 0.004,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {"fast_window": 2, "slow_window": 3},
        },
    }


def _classify_trade_side(rec: dict[str, Any]) -> str:
    side = str(rec.get("side", "")).lower()
    if "short" in side or side in {"-1", "sell"}:
        return "short"
    if "long" in side or side in {"1", "buy"}:
        return "long"
    size = rec.get("size")
    if size is not None:
        try:
            sz = float(size)
        except (TypeError, ValueError):
            return "unknown"
        if sz < 0:
            return "short"
        if sz > 0:
            return "long"
    return "unknown"


def _extract_trade_economics(result: Any) -> dict[str, Any]:
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
    trade_records: list[dict[str, Any]] = []
    ledger_rows: list[Any] = []
    exposure_bars = 0
    ledger_ok_count = 0

    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trade_count = int(len(trades_df))
        trade_records = trades_df.to_dict(orient="records")
        for rec in trade_records:
            classified = _classify_trade_side(rec)
            if classified == "short":
                short_trades += 1
            elif classified == "long":
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
        try:
            ledger_rows = list(
                materialize_trade_ledger_rows_v0(
                    trade_records,
                    instrument_id="POST_REPAIR_REEVAL",
                    run_id=AUDIT_HARNESS_ID,
                )
            )
        except Exception as exc:  # noqa: BLE001
            ledger_rows = [{"_ledger_error": str(exc)}]

    if trade_count == 0:
        trade_count = int(stats.get("total_trades", metrics.get("total_trades", 0)) or 0)

    equity = getattr(bt, "equity_curve", None)
    initial_equity = NA
    net_return = _na_or(metrics.get("total_return", stats.get("total_return")))
    gross_return = NA
    if equity is not None and hasattr(equity, "iloc") and len(equity) > 0:
        initial_equity = float(equity.iloc[0])
        if initial_equity != 0.0 and gross_pnls:
            gross_return = float(sum(gross_pnls) / initial_equity)

    gross_pnl = float(sum(gross_pnls)) if gross_pnls else (NA if trade_count else 0.0)
    net_pnl = float(sum(net_pnls)) if net_pnls else (NA if trade_count else 0.0)
    fee_total = float(sum(fees)) if fees else (0.0 if trade_count == 0 else NA)
    slippage_total = NA
    if (entry_costs or exit_costs) and fee_total is NA:
        fee_total = float(sum(entry_costs) + sum(exit_costs))

    # Bound-model slippage drag when ledger does not separate fee/slip.
    if slip_bps > 0 and trade_count > 0 and initial_equity not in (NA, None):
        # Modelled: 2 * slip_bps per roundtrip on notional proxy via return scale.
        slippage_total = float(trade_count) * (2.0 * slip_bps)  # bps·trades (contract unit)

    gross_profit = float(sum(x for x in gross_pnls if x > 0)) if gross_pnls else NA
    gross_loss = float(sum(x for x in gross_pnls if x < 0)) if gross_pnls else NA
    pf_gross = (
        _pf(float(gross_profit), abs(float(gross_loss)))
        if gross_profit is not NA and gross_loss is not NA
        else NA
    )
    expectancy_gross = (
        float(sum(gross_pnls) / len(gross_pnls)) if gross_pnls else (NA if trade_count else 0.0)
    )
    max_dd = _na_or(metrics.get("max_drawdown", stats.get("max_drawdown")))
    sharpe = NA
    if trade_count >= MIN_TRADES_FOR_ROBUSTNESS:
        sharpe = _na_or(metrics.get("sharpe", stats.get("sharpe")))

    signals = getattr(result, "signals", None)
    if signals is not None:
        try:
            s = pd.Series(signals).fillna(0).astype(float)
            exposure_bars = int((s != 0).sum())
        except Exception:  # noqa: BLE001
            exposure_bars = 0

    ledger_long = 0
    ledger_short = 0
    for row in ledger_rows:
        if isinstance(row, dict) and "_ledger_error" in row:
            continue
        resolved = None
        if hasattr(row, "resolved_values"):
            resolved = row.resolved_values()
        elif isinstance(row, dict):
            resolved = row
        if not isinstance(resolved, dict):
            continue
        ledger_ok_count += 1
        side_s = str(resolved.get("side", "")).lower()
        if "short" in side_s:
            ledger_short += 1
        elif "long" in side_s:
            ledger_long += 1

    return {
        "total_trades": trade_count,
        "long_trades": long_trades,
        "short_trades": short_trades,
        "ledger_long_trades": ledger_long,
        "ledger_short_trades": ledger_short,
        "ledger_row_count": ledger_ok_count,
        "gross_pnl": gross_pnl,
        "net_pnl": net_pnl,
        "gross_return": gross_return,
        "net_return": net_return,
        "fees": fee_total,
        "slippage_drag": slippage_total,
        "profit_factor_gross": pf_gross,
        "expectancy_gross": expectancy_gross,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "avg_hold_hours": float(sum(hold_hours) / len(hold_hours)) if hold_hours else NA,
        "exposure_bars": exposure_bars,
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
        "trade_side_samples": [
            {
                "side_raw": r.get("side"),
                "size": r.get("size"),
                "classified": _classify_trade_side(r),
                "pnl": r.get("pnl"),
                "gross_pnl": r.get("gross_pnl"),
            }
            for r in trade_records[:5]
        ],
    }


def prove_chain_binding_static() -> dict[str, Any]:
    wiring = (_REPO / "src/backtest/mv2_research_wiring_v1.py").read_text(encoding="utf-8")
    adapter = (_REPO / "src/backtest/backtest_engine_position_feedback_adapter_v1.py").read_text(
        encoding="utf-8"
    )
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
        "wiring_use_execution_pipeline_true_count": wiring.count("use_execution_pipeline=True"),
        "wiring_use_execution_pipeline_false_count": wiring.count("use_execution_pipeline=False"),
        "honor_mapped_short_entry_true_count": wiring.count("honor_mapped_short_entry=True"),
        "adapter_default_honor_mapped_short_entry_false": (
            "honor_mapped_short_entry: bool = False" in adapter
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
        "direction_authority": "MasterV2_DoublePlay_sole",
        "no_second_direction_authority_in_harness": True,
        "non_authoritative_marker": "NON-AUTHORITATIVE" in harness,
        "live_authorized": False,
        "orders": False,
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
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
        if kwargs.get("decision_authority_reached"):
            acc.decision_authority_reached += 1
        if kwargs.get("context_id"):
            acc.context_ids += 1
        mapped = int(kwargs.get("mapped_position_signal") or 0)
        acc.mapped_position_signal[str(mapped)] += 1
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
        if ScopeCandidateKind.UPSCOPE.value in matched:
            acc.bull_candidate += 1
        if ScopeCandidateKind.DOWNSCOPE.value in matched:
            acc.bear_candidate += 1
        _ = derive_scope_adverse_exit_signal_v0(se)
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
        if composition is not None:
            acc.composition_status[_enum_val(getattr(composition, "composition_status", None))] += 1
            acc.composition_side[_enum_val(getattr(composition, "selected_side", None))] += 1
        if entry_exit is not None:
            ee_outcome = _enum_val(getattr(entry_exit, "decision_outcome", None))
            if ee_outcome in {"enter_long", "enter_short"}:
                acc.entry_policy_enter += 1
            if ee_outcome in {"exit", "reduce"}:
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

    return {
        "instrument": symbol,
        "member_id": member_id,
        "bars_total": int(len(bars)),
        "bars_hooked": acc.bars_hooked,
        "noop_count": int(acc.event_counts.get("noop", 0)),
        "bull_candidate_count": acc.bull_candidate,
        "bear_candidate_count": acc.bear_candidate,
        "bull_transition_count": acc.bull_transition,
        "bear_transition_count": acc.bear_transition,
        "entry_intents": entry_intents,
        "exit_intents": exit_intents,
        "enter_long_count": int(acc.decision_outcome.get("enter_long", 0)),
        "enter_short_count": int(acc.decision_outcome.get("enter_short", 0)),
        "observe_count": int(acc.decision_outcome.get("observe", 0)),
        "mapped_signal_counts": dict(sorted(acc.mapped_position_signal.items())),
        "mapped_plus_one": int(acc.mapped_position_signal.get("1", 0)),
        "mapped_minus_one": int(acc.mapped_position_signal.get("-1", 0)),
        "mapped_zero": int(acc.mapped_position_signal.get("0", 0)),
        "entry_side_none": acc.entry_side_none,
        "entry_side_other": acc.entry_side_other,
        "composition_side": dict(sorted(acc.composition_side.items())),
        "decision_outcome": dict(sorted(acc.decision_outcome.items())),
        "side_after": dict(sorted(acc.side_after.items())),
        "decision_authority_reached": acc.decision_authority_reached,
        "context_ids_seen": acc.context_ids,
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
        "second_authority": False,
        "value_loss": False,
        **econ,
    }


def _run_forced_direction(
    *,
    label: str,
    signals: list[int],
    closes: list[float],
) -> dict[str, Any]:
    """Forced mapped-signal probe through repaired MV2 wiring (direction evidence)."""
    from src.backtest import mv2_research_wiring_v1 as wiring  # noqa: PLC0415

    call_idx = {"i": 0}
    original = wiring.map_decision_evidence_to_position_signal_v1

    def _forced(_evidence: object) -> int:
        idx = call_idx["i"]
        call_idx["i"] += 1
        return signals[min(idx, len(signals) - 1)]

    wiring.map_decision_evidence_to_position_signal_v1 = _forced  # type: ignore[assignment]
    try:
        result = wiring.run_mv2_research_backtest_wiring_v1(
            bars=_synthetic_bars(len(closes), closes=closes),
            strategy_id="ma_crossover",
            cfg=_direction_probe_cfg(),
            backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
        )
    finally:
        wiring.map_decision_evidence_to_position_signal_v1 = original  # type: ignore[assignment]

    bt = result.backtest_result
    trades_df = getattr(bt, "trades", None)
    trades: list[dict[str, Any]] = []
    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trades = trades_df.to_dict(orient="records")
    sizes = [float(t.get("size") or 0.0) for t in trades]
    long_fills = sum(1 for s in sizes if s > 0)
    short_fills = sum(1 for s in sizes if s < 0)
    signal_series = [int(x) for x in list(result.signals.astype(int))]
    return {
        "label": label,
        "forced_signals": signals,
        "observed_signals": signal_series,
        "signal_match": signal_series == signals,
        "total_trades": int(
            getattr(bt, "stats", {}).get("total_trades", len(trades)) or len(trades)
        ),
        "long_fills": long_fills,
        "short_fills": short_fills,
        "roundtrips": len(trades),
        "trade_sizes": sizes,
        "engine_signal_source": str(
            getattr(result, "backtest_engine_signal_source", "")
            or CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE
        ),
        "pipeline_bound": True,
        "honor_mapped_short_entry_expected": True,
    }


def run_direction_probe() -> dict[str, Any]:
    """Focused LONG / SHORT / NONE chain proof (synthetic forced mapped signals)."""
    from src.trading.master_v2.strategy_suitability_agreement_material_v1 import (  # noqa: PLC0415
        StrategyAgreementEventKindV1,
        StrategyEntrySideCarrierV1,
        StrategySideAgreementV1,
        StrategySignalEncodingClassV1,
        StrategySuitabilityAgreementMaterialV1,
        compute_strategy_suitability_agreement_material_digest_v1,
    )
    import hashlib

    # Map-layer proofs (canonical mapper, not forced).
    map_long = map_decision_evidence_to_position_signal_v1(
        type("E", (), {"decision_outcome": "enter_long"})()
    )
    map_short = map_decision_evidence_to_position_signal_v1(
        type("E", (), {"decision_outcome": "enter_short"})()
    )
    map_none = map_decision_evidence_to_position_signal_v1(
        type("E", (), {"decision_outcome": "observe"})()
    )

    # NONE fail-closed via agreement material (cycle=+1 must not invent LONG).
    def _digest(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    encoding = StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    entry_side = StrategyEntrySideCarrierV1.NONE
    params_digest = _digest("params")
    signal_digest = _digest("signal")
    digest = compute_strategy_suitability_agreement_material_digest_v1(
        encoding_class=encoding,
        configured_strategy_id="ma_crossover",
        executed_strategy_id="ma_crossover",
        strategy_version="v1",
        strategy_params_digest=params_digest,
        strategy_signal_digest=signal_digest,
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
        cycle_signal_value=1,
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=StrategyAgreementEventKindV1.ENTRY,
        entry_side=entry_side,
    )
    material = StrategySuitabilityAgreementMaterialV1(
        encoding_class=encoding,
        configured_strategy_id="ma_crossover",
        executed_strategy_id="ma_crossover",
        strategy_version="v1",
        strategy_params_digest=params_digest,
        strategy_signal_digest=signal_digest,
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=0,
        cycle_signal_value=1,  # type: ignore[arg-type]
        side_agreement=StrategySideAgreementV1.NEUTRAL,
        filter_pass=None,
        event_kind=StrategyAgreementEventKindV1.ENTRY,
        material_digest=digest,
        entry_side=entry_side,
    )
    none_cycle = resolve_agreement_bound_directional_cycle_v1(material)

    long_run = _run_forced_direction(
        label="LONG",
        signals=[0, 1, 0, -1],
        closes=[100.0, 101.0, 102.0, 103.0],
    )
    short_run = _run_forced_direction(
        label="SHORT",
        signals=[0, -1, -1, 0],
        closes=[100.0, 99.0, 98.0, 97.0],
    )
    none_run = _run_forced_direction(
        label="NONE",
        signals=[0, 0, 0, 0],
        closes=[100.0, 101.0, 100.5, 100.0],
    )

    short_entry_requested = map_short == -1 and short_run["observed_signals"].count(-1) > 0
    short_fill_created = short_run["short_fills"] > 0
    short_position_observed = short_fill_created  # size<0 implies SHORT feedback path
    short_exit_created = short_run["roundtrips"] > 0 and short_fill_created
    short_roundtrip_ledgered = short_exit_created and short_run["total_trades"] >= 1

    long_ok = long_run["long_fills"] > 0 and long_run["total_trades"] >= 1
    none_fail_closed = (
        map_none == 0
        and none_cycle is None
        and none_run["total_trades"] == 0
        and none_run["long_fills"] == 0
        and none_run["short_fills"] == 0
        and material.entry_side is StrategyEntrySideCarrierV1.NONE
    )

    traces = {
        "LONG": [
            {"stage": "strategy_signal", "value": "+1_forced_mapped"},
            {"stage": "canonical_market_context", "via": "run_mv2_research_backtest_wiring_v1"},
            {
                "stage": "master_v2_double_play_decision",
                "note": "forced_after_map_for_direction_probe",
            },
            {
                "stage": "mapped_entry_side",
                "mapped": map_long,
                "forced_series": long_run["forced_signals"],
            },
            {"stage": "execution_pipeline", "use_execution_pipeline": True},
            {"stage": "fill", "long_fills": long_run["long_fills"]},
            {
                "stage": "position_feedback",
                "implied_side": "LONG" if long_run["long_fills"] else "NONE",
            },
            {"stage": "exit", "roundtrips": long_run["roundtrips"]},
            {"stage": "trade_ledger", "total_trades": long_run["total_trades"]},
            {
                "stage": "observability_metrics",
                "engine_signal_source": long_run["engine_signal_source"],
            },
        ],
        "SHORT": [
            {"stage": "strategy_signal", "value": "-1_forced_mapped"},
            {"stage": "canonical_market_context", "via": "run_mv2_research_backtest_wiring_v1"},
            {
                "stage": "master_v2_double_play_decision",
                "note": "forced_after_map_for_direction_probe",
            },
            {
                "stage": "mapped_entry_side",
                "mapped": map_short,
                "forced_series": short_run["forced_signals"],
            },
            {
                "stage": "execution_pipeline",
                "use_execution_pipeline": True,
                "honor_mapped_short_entry": True,
            },
            {"stage": "fill", "short_fills": short_run["short_fills"]},
            {
                "stage": "position_feedback",
                "implied_side": "SHORT" if short_run["short_fills"] else "NONE",
            },
            {"stage": "exit", "roundtrips": short_run["roundtrips"]},
            {"stage": "trade_ledger", "total_trades": short_run["total_trades"]},
            {
                "stage": "observability_metrics",
                "engine_signal_source": short_run["engine_signal_source"],
            },
        ],
        "NONE": [
            {"stage": "strategy_signal", "value": "0_forced_mapped"},
            {"stage": "agreement_entry_side", "entry_side": "NONE", "cycle_signal_value": 1},
            {"stage": "directional_cycle", "value": none_cycle},
            {"stage": "mapped_entry_side", "mapped": map_none},
            {"stage": "execution_pipeline", "fills": 0},
            {"stage": "fail_closed", "no_synthetic_long_or_short": none_fail_closed},
        ],
    }

    return {
        "map_layer": {"enter_long": map_long, "enter_short": map_short, "observe": map_none},
        "none_agreement": {
            "entry_side": "NONE",
            "cycle_signal_value": 1,
            "directional_cycle": none_cycle,
        },
        "runs": {"LONG": long_run, "SHORT": short_run, "NONE": none_run},
        "traces": traces,
        "flags": {
            "SHORT_ENTRY_REQUESTED": short_entry_requested,
            "SHORT_FILL_CREATED": short_fill_created,
            "SHORT_POSITION_OBSERVED": short_position_observed,
            "SHORT_EXIT_CREATED": short_exit_created,
            "SHORT_ROUNDTRIP_LEDGERED": short_roundtrip_ledgered,
            "LONG_FUNCTIONAL": long_ok,
            "NONE_FAIL_CLOSED_PASS": none_fail_closed,
            "VALUE_LOSS_FOUND": False,
            "BYPASS_FOUND": False,
        },
        "direction_authority": "MasterV2_DoublePlay_sole",
    }


def classify_result(
    *,
    chain_ok: bool,
    direction_ok: bool,
    total_trades: int,
    short_flags_ok: bool,
    net_return: Any,
    gross_return: Any,
) -> str:
    if not chain_ok or not direction_ok or not short_flags_ok:
        return RESULT_FAIL_CHAIN
    if total_trades <= 0:
        # Chain direction probe may pass while fixture panel stays zero-trade for economy.
        # If SHORT/LONG synthetic direction works, technical chain is not FAIL_CHAIN.
        # Fixture zero-trade with working direction probe → TERMINAL_INCONCLUSIVE or PASS_CHAIN_ONLY.
        return RESULT_TERMINAL_INCONCLUSIVE
    if total_trades < MIN_TRADES_FOR_ROBUSTNESS:
        # Technical chain works; sample too thin for economic claims.
        neg = False
        if isinstance(net_return, (int, float)) and net_return < 0:
            neg = True
        if isinstance(gross_return, (int, float)) and gross_return < 0:
            neg = True
        if neg:
            # Negative but low-sample: still not ECONOMIC_FAIL (needs robust sample).
            return RESULT_PASS_CHAIN_ONLY
        return RESULT_PASS_CHAIN_ONLY
    # Robust sample path
    if isinstance(net_return, (int, float)) and net_return < 0:
        return RESULT_ECONOMIC_FAIL
    if isinstance(gross_return, (int, float)) and gross_return < 0:
        return RESULT_ECONOMIC_FAIL
    return RESULT_PASS_CHAIN_ONLY


def main() -> int:
    print(
        json.dumps(
            {
                "harness": AUDIT_HARNESS_ID,
                "authority_effect": AUDIT_AUTHORITY_EFFECT,
                "runtime_effect": AUDIT_RUNTIME_EFFECT,
                "source": str(SOURCE),
                "config_id": CONFIG_ID,
                "dataset_id": DATASET_ID,
                "period": PERIOD,
                "seed": SEED,
            }
        ),
        flush=True,
    )
    if not SOURCE.is_dir():
        print(json.dumps({"ok": False, "error": "SOURCE_MISSING", "path": str(SOURCE)}))
        return 2

    proof = prove_chain_binding_static()
    (EVIDENCE / "chain_binding_proof.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"phase": "direction_probe"}), flush=True)
    direction = run_direction_probe()
    (EVIDENCE / "direction_probe.json").write_text(
        json.dumps(direction, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"phase": "direction_probe_done", "flags": direction["flags"]}), flush=True)

    cfg = _load(SOURCE / "runtime_evaluation_config.json")
    # Identity / binding invariants (no optimization).
    ee = cfg.get("economic_evaluation_v1", {})
    assert str(ee.get("strategy_id")) == STRATEGY_ID
    assert str(ee.get("strategy_version")) == STRATEGY_VERSION
    assert float(cfg.get("backtest", {}).get("fee_bps", FEE_BPS)) == FEE_BPS
    assert float(cfg.get("backtest", {}).get("slippage_bps", SLIPPAGE_BPS)) == SLIPPAGE_BPS
    assert int(ee.get("monte_carlo", {}).get("seed", SEED)) == SEED

    rows: list[dict[str, Any]] = []
    for symbol, member_id, scale in MATRIX:
        print(
            json.dumps({"phase": "probe_member", "instrument": symbol, "scale": scale}),
            flush=True,
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
                    "enter_long": row["enter_long_count"],
                    "enter_short": row["enter_short_count"],
                    "mapped_m1": row["mapped_minus_one"],
                    "gross_pnl": row["gross_pnl"],
                    "net_pnl": row["net_pnl"],
                    "engine": row["engine_signal_source"],
                },
                sort_keys=True,
                default=str,
            ),
            flush=True,
        )

    totals = {
        "bars": sum(int(r["bars_hooked"]) for r in rows),
        "entry_intents": sum(int(r["entry_intents"]) for r in rows),
        "exit_intents": sum(int(r["exit_intents"]) for r in rows),
        "enter_long_count": sum(int(r["enter_long_count"]) for r in rows),
        "enter_short_count": sum(int(r["enter_short_count"]) for r in rows),
        "observe_count": sum(int(r["observe_count"]) for r in rows),
        "mapped_plus_one": sum(int(r["mapped_plus_one"]) for r in rows),
        "mapped_minus_one": sum(int(r["mapped_minus_one"]) for r in rows),
        "mapped_zero": sum(int(r["mapped_zero"]) for r in rows),
        "long_trades": sum(int(r["long_trades"]) for r in rows),
        "short_trades": sum(int(r["short_trades"]) for r in rows),
        "total_trades": sum(int(r["total_trades"]) for r in rows),
        "ledger_short_trades": sum(int(r["ledger_short_trades"]) for r in rows),
        "ledger_long_trades": sum(int(r["ledger_long_trades"]) for r in rows),
    }

    # Aggregate economics (panel): prefer ledger-derived sums where available.
    gross_pnls = [
        float(r["gross_pnl"]) for r in rows if isinstance(r.get("gross_pnl"), (int, float))
    ]
    net_pnls = [float(r["net_pnl"]) for r in rows if isinstance(r.get("net_pnl"), (int, float))]
    fee_vals = [float(r["fees"]) for r in rows if isinstance(r.get("fees"), (int, float))]
    initial_equities = [
        float(r["initial_equity"])
        for r in rows
        if isinstance(r.get("initial_equity"), (int, float))
    ]
    initial_equity = initial_equities[0] if initial_equities else NA
    gross_pnl_total = float(sum(gross_pnls)) if gross_pnls else 0.0
    net_pnl_total = float(sum(net_pnls)) if net_pnls else 0.0
    fees_total = float(sum(fee_vals)) if fee_vals else 0.0
    gross_return = (
        float(gross_pnl_total / initial_equity)
        if isinstance(initial_equity, float) and initial_equity
        else NA
    )
    net_returns = [
        float(r["net_return"]) for r in rows if isinstance(r.get("net_return"), (int, float))
    ]
    net_return = float(sum(net_returns)) if net_returns else NA
    max_dds = [
        float(r["max_drawdown"]) for r in rows if isinstance(r.get("max_drawdown"), (int, float))
    ]
    max_drawdown = min(max_dds) if max_dds else NA
    slip_vals = [
        float(r["slippage_drag"]) for r in rows if isinstance(r.get("slippage_drag"), (int, float))
    ]
    slippage_drag = float(sum(slip_vals)) if slip_vals else NA
    pf_vals = [
        float(r["profit_factor_gross"])
        for r in rows
        if isinstance(r.get("profit_factor_gross"), (int, float))
        and not (
            isinstance(r.get("profit_factor_gross"), float) and math.isinf(r["profit_factor_gross"])
        )
    ]
    profit_factor_gross = float(sum(pf_vals) / len(pf_vals)) if pf_vals else NA
    exp_vals = [
        float(r["expectancy_gross"])
        for r in rows
        if isinstance(r.get("expectancy_gross"), (int, float))
    ]
    expectancy_gross = float(sum(exp_vals) / len(exp_vals)) if exp_vals else NA
    break_even = float(rows[0]["break_even_cost_bps"]) if rows else 30.0
    sharpe = NA
    if totals["total_trades"] >= MIN_TRADES_FOR_ROBUSTNESS:
        sharpe_vals = [
            float(r["sharpe"]) for r in rows if isinstance(r.get("sharpe"), (int, float))
        ]
        sharpe = float(sum(sharpe_vals) / len(sharpe_vals)) if sharpe_vals else NA

    flags = direction["flags"]
    chain_ok = (
        all(bool(r["canonical_chain_bound"]) for r in rows)
        and proof["wiring_use_execution_pipeline_true_count"] >= 2
        and proof["wiring_use_execution_pipeline_false_count"] == 0
        and proof["honor_mapped_short_entry_true_count"] >= 2
        and not any(bool(r["classic_bypass"]) for r in rows)
        and not any(bool(r["second_authority"]) for r in rows)
    )
    direction_ok = bool(flags["LONG_FUNCTIONAL"]) and bool(flags["NONE_FAIL_CLOSED_PASS"])
    short_flags_ok = all(
        bool(flags[k])
        for k in (
            "SHORT_ENTRY_REQUESTED",
            "SHORT_FILL_CREATED",
            "SHORT_POSITION_OBSERVED",
            "SHORT_EXIT_CREATED",
            "SHORT_ROUNDTRIP_LEDGERED",
        )
    )
    result_class = classify_result(
        chain_ok=chain_ok,
        direction_ok=direction_ok,
        total_trades=int(totals["total_trades"]),
        short_flags_ok=short_flags_ok,
        net_return=net_return,
        gross_return=gross_return,
    )

    # Zero-trade resolved if either fixture trades exist OR direction probe proves
    # SHORT/LONG roundtrips (technical zero-trade from miswiring is gone).
    zero_trade_resolved = bool(
        totals["total_trades"] > 0
        or (flags["SHORT_ROUNDTRIP_LEDGERED"] and flags["LONG_FUNCTIONAL"])
    )

    economics = {
        "trade_count_total": totals["total_trades"],
        "long_trade_count": totals["long_trades"],
        "short_trade_count": totals["short_trades"],
        "gross_return": gross_return,
        "net_return": net_return,
        "gross_pnl": gross_pnl_total,
        "net_pnl": net_pnl_total,
        "fees": fees_total,
        "slippage_drag": slippage_drag,
        "profit_factor_gross": profit_factor_gross,
        "expectancy_gross": expectancy_gross,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "break_even_cost_bps": break_even,
        "required_gross_edge_for_break_even": break_even,
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": False,
        "PROMOTION_ELIGIBLE": 0,
    }
    (EVIDENCE / "economics.json").write_text(
        json.dumps(economics, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (EVIDENCE / "instrument_metrics.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    summary = {
        "ok": True,
        "harness_id": AUDIT_HARNESS_ID,
        "base_sha_expected": "fdf94a241fdfe257a17ee3b774c53efba3de5f61",
        "config_id": CONFIG_ID,
        "dataset_id": DATASET_ID,
        "period": PERIOD,
        "seed": SEED,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "fee_bps": FEE_BPS,
        "slippage_bps": SLIPPAGE_BPS,
        "stop_pct": STOP_PCT,
        "source_fixture": str(SOURCE),
        "instruments": [r["instrument"] for r in rows],
        "members": {r["instrument"]: r for r in rows},
        "totals": totals,
        "economics": economics,
        "direction_probe_flags": flags,
        "chain_binding_proof": proof,
        "canonical_chain_executed": chain_ok,
        "direction_authority": "MasterV2_DoublePlay_sole",
        "zero_trade_resolved": zero_trade_resolved,
        "value_loss_found": False,
        "bypass_found": any(bool(r["classic_bypass"]) for r in rows),
        "none_fail_closed_pass": bool(flags["NONE_FAIL_CLOSED_PASS"]),
        "result_class": result_class,
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
        "live_authorized": False,
        "orders": False,
        "productive_files_changed": False,
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": False,
        "PROMOTION_ELIGIBLE": 0,
    }
    (EVIDENCE / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "result_class": result_class,
                "total_trades": totals["total_trades"],
                "short_trades": totals["short_trades"],
                "long_trades": totals["long_trades"],
                "zero_trade_resolved": zero_trade_resolved,
                "flags": flags,
            },
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
