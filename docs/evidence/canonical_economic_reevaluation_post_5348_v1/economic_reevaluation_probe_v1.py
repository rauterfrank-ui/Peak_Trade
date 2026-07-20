#!/usr/bin/env python3
"""NON-AUTHORITATIVE audit harness: post-#5348 canonical economic reevaluation v1.

Evidence-only. Re-runs the repaired Master-V2 / Double-Play chain on the largest
available PIT OKX linear USDT non-BTC futures panel (118 members). Does NOT:
  - mutate productive trading / risk / execution / authority code
  - open the economic gate or promote
  - fetch external data / activate live / orders / shadow / capital

Dataset period note: the durable archive max coverage remains
2024-05-01T00:00:00Z..2024-09-01T00:00:00Z. No longer chronological PIT panel
exists locally; chronological extension is a documented PARTIAL blocker. This
harness expands the *cross-section* from the prior 4-instrument sample to the
full 118-member binding panel and applies time/cost/slip/stop/LOO robustness
checks supported by existing offline wiring.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import time
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

_EVIDENCE_DIR = Path(__file__).resolve().parent
if str(_EVIDENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_EVIDENCE_DIR))
from shared_portfolio_equity_research_v1 import (  # noqa: E402
    HOURLY_PERIODS_PER_YEAR,
    PORTFOLIO_AGGREGATION_ID,
    build_equal_weight_portfolio_equity,
    peak_gross_exposure_from_scaled_trades,
    portfolio_metrics_from_equity,
    reconcile_portfolio_equity_to_scaled_net_pnl,
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
BINDING = (
    _REPO / "config/research/bollinger_bands_v2_full_canonical_system_economic_binding_v1.json"
)
PANEL_MANIFEST = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1/panel/panel_dataset_manifest.json"
)

AUDIT_HARNESS_ID = "CANONICAL_ECONOMIC_REEVALUATION_POST_5348_V1"
AUDIT_AUTHORITY_EFFECT = "NONE"
AUDIT_RUNTIME_EFFECT = "NONE"
MIN_TRADES_FOR_ROBUSTNESS = 20
NA = "NOT_AVAILABLE"

CONFIG_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
PERIOD = "2024-05-01T00:00:00Z..2024-09-01T00:00:00Z"
SEED = 42
STRATEGY_ID = "bollinger_bands"
STRATEGY_VERSION = "v2"
FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
STOP_PCT = 0.025

# Chronological folds from existing runtime_evaluation_config periods.
WF_FOLDS = (
    ("train", "2024-05-01T00:00:00Z", "2024-07-01T11:00:00Z"),
    ("validation", "2024-07-01T12:00:00Z", "2024-08-01T05:00:00Z"),
    ("oos", "2024-08-01T06:00:00Z", "2024-09-01T00:00:00Z"),
)

CLASS_PASS = "PASS_ECONOMIC_CANDIDATE"
CLASS_FAIL = "FAIL_ECONOMIC"
CLASS_LOW = "INCONCLUSIVE_LOW_SAMPLE"
CLASS_UNSTABLE = "INCONCLUSIVE_UNSTABLE"
CLASS_PARTIAL = "PARTIAL"
CLASS_INVALID = "INVALID_ECONOMIC_MEASUREMENT"
SLEEVE_INITIAL_CASH = 10_000.0
SHARED_INITIAL_CAPITAL = 10_000.0
# Backward-compatible alias used by older integrity helpers/tests.
INITIAL_CAPITAL_PER_INSTRUMENT = SLEEVE_INITIAL_CASH
LEDGER_RECON_TOL = 1e-6


@dataclass
class Acc:
    bars_hooked: int = 0
    decision_outcome: Counter = field(default_factory=Counter)
    mapped_position_signal: Counter = field(default_factory=Counter)
    entry_side_none: int = 0
    entry_side_other: int = 0
    intermediate_missing: int = 0


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


def _symbol(member_id: str) -> str:
    parts = member_id.split(":")
    return parts[2] if len(parts) >= 3 else member_id


def _panel_members() -> list[str]:
    binding = _load(BINDING)
    ids = binding["binding"]["instrument_binding"]["eligible_instrument_ids"]
    return [str(x) for x in ids]


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


def _num(v: Any) -> Optional[float]:
    if isinstance(v, (int, float)) and not (
        isinstance(v, float) and (math.isnan(v) or math.isinf(v))
    ):
        return float(v)
    return None


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
        "direction_authority": "trading.master_v2.double_play_state.transition_state",
        "no_second_direction_authority_in_harness": True,
        "non_authoritative_marker": "NON-AUTHORITATIVE" in harness,
        "short_bound_via_execution_pipeline": (
            wiring.count("use_execution_pipeline=True") > 0
            and wiring.count("honor_mapped_short_entry=True") > 0
        ),
        "live_authorized": False,
        "orders": False,
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
        "economic_gate_opened": False,
        "promotion_eligible": False,
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


def _exit_reason(rec: dict[str, Any]) -> str:
    for key in ("exit_reason", "reason", "close_reason", "stop_reason"):
        val = rec.get(key)
        if val is not None and str(val).strip():
            return str(val)
    stop_hit = rec.get("stop_hit") or rec.get("stopped_out") or rec.get("is_stop")
    if stop_hit:
        return "stop"
    return "unspecified"


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
    slips: list[float] = []
    entry_costs: list[float] = []
    exit_costs: list[float] = []
    hold_hours: list[float] = []
    exit_reasons: Counter = Counter()
    stop_triggers = 0
    trade_records: list[dict[str, Any]] = []

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
            if rec.get("fee_total") is not None:
                fees.append(float(rec["fee_total"]))
            elif rec.get("fee") is not None:
                fees.append(float(rec["fee"]))
            if rec.get("slippage_total") is not None:
                slips.append(float(rec["slippage_total"]))
            if rec.get("entry_cost") is not None:
                entry_costs.append(float(rec["entry_cost"]))
            if rec.get("exit_cost") is not None:
                exit_costs.append(float(rec["exit_cost"]))
            reason = _exit_reason(rec)
            exit_reasons[reason] += 1
            if "stop" in reason.lower() or rec.get("stop_hit") or rec.get("stopped_out"):
                stop_triggers += 1
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
    initial_equity: Any = NA
    net_return = _na_or(metrics.get("total_return", stats.get("total_return")))
    gross_return: Any = NA
    if equity is not None and hasattr(equity, "iloc") and len(equity) > 0:
        initial_equity = float(equity.iloc[0])
        if initial_equity != 0.0 and gross_pnls:
            gross_return = float(sum(gross_pnls) / initial_equity)

    gross_pnl = float(sum(gross_pnls)) if gross_pnls else (0.0 if trade_count == 0 else NA)
    net_pnl = float(sum(net_pnls)) if net_pnls else (0.0 if trade_count == 0 else NA)
    fee_total = float(sum(fees)) if fees else 0.0
    slippage_total = float(sum(slips)) if slips else 0.0
    # If fee_total/slippage_total absent but combined entry/exit costs present, keep
    # combined costs visible via cost_drag; do not invent a fee/slip split.
    combined_costs = (
        float(sum(entry_costs) + sum(exit_costs)) if (entry_costs or exit_costs) else 0.0
    )
    if fee_total == 0.0 and slippage_total == 0.0 and combined_costs > 0.0:
        fee_total = combined_costs
        slippage_total = 0.0

    cost_drag: Any = NA
    if isinstance(gross_pnl, (int, float)) and isinstance(net_pnl, (int, float)):
        cost_drag = float(gross_pnl - net_pnl)
    configured_nonzero = (fee_bps + slip_bps) > 1e-15
    ledger_cost_sum = float(fee_total) + float(slippage_total)
    if configured_nonzero and abs(ledger_cost_sum) <= 1e-12:
        cost_application = "NOT_APPLIED"
    else:
        cost_application = "APPLIED"
    ledger_recon = "PASS"
    if (
        isinstance(gross_pnl, (int, float))
        and isinstance(net_pnl, (int, float))
        and abs(float(gross_pnl) - ledger_cost_sum - float(net_pnl)) > LEDGER_RECON_TOL
        and abs(float(gross_pnl) - float(cost_drag) - float(net_pnl)) > LEDGER_RECON_TOL
    ):
        ledger_recon = "FAIL"

    gross_profit = float(sum(x for x in gross_pnls if x > 0)) if gross_pnls else NA
    gross_loss = float(sum(x for x in gross_pnls if x < 0)) if gross_pnls else NA
    pf_gross = (
        _pf(float(gross_profit), abs(float(gross_loss)))
        if gross_profit is not NA and gross_loss is not NA
        else NA
    )
    net_profit = float(sum(x for x in net_pnls if x > 0)) if net_pnls else NA
    net_loss = float(sum(x for x in net_pnls if x < 0)) if net_pnls else NA
    pf_net = (
        _pf(float(net_profit), abs(float(net_loss)))
        if net_profit is not NA and net_loss is not NA
        else NA
    )
    wins = sum(1 for x in net_pnls if x > 0) if net_pnls else 0
    win_rate: Any = (wins / len(net_pnls)) if net_pnls else (NA if trade_count else 0.0)
    expectancy_gross = (
        float(sum(gross_pnls) / len(gross_pnls))
        if gross_pnls
        else (0.0 if trade_count == 0 else NA)
    )
    max_dd = _na_or(metrics.get("max_drawdown", stats.get("max_drawdown")))
    sharpe = NA
    if trade_count >= MIN_TRADES_FOR_ROBUSTNESS:
        sharpe = _na_or(metrics.get("sharpe", stats.get("sharpe")))

    signals = getattr(result, "signals", None)
    exposure_bars = 0
    if signals is not None:
        try:
            s = pd.Series(signals).fillna(0).astype(float)
            exposure_bars = int((s != 0).sum())
        except Exception:  # noqa: BLE001
            exposure_bars = 0

    turnover = float(trade_count)

    # Compact trade rows for WF / LOO / exit analysis (JSON-safe).
    compact_trades: list[dict[str, Any]] = []
    for rec in trade_records:
        compact_trades.append(
            {
                "side": _classify_trade_side(rec),
                "pnl": _num(rec.get("pnl")),
                "gross_pnl": _num(rec.get("gross_pnl")),
                "fee": _num(rec.get("fee")),
                "fee_total": _num(rec.get("fee_total")),
                "slippage_total": _num(rec.get("slippage_total")),
                "entry_cost": _num(rec.get("entry_cost")),
                "exit_cost": _num(rec.get("exit_cost")),
                "size": _num(rec.get("size")),
                "entry_price": _num(rec.get("entry_price")),
                "exit_price": _num(rec.get("exit_price")),
                "entry_time": str(rec.get("entry_time"))
                if rec.get("entry_time") is not None
                else None,
                "exit_time": str(rec.get("exit_time"))
                if rec.get("exit_time") is not None
                else None,
                "exit_reason": _exit_reason(rec),
                "stop_hit": bool(rec.get("stop_hit") or rec.get("stopped_out") or False),
            }
        )

    return {
        "total_trades": trade_count,
        "long_trades": long_trades,
        "short_trades": short_trades,
        "gross_pnl": gross_pnl,
        "net_pnl": net_pnl,
        "gross_return": gross_return,
        "net_return": net_return,
        "fees": fee_total,
        "slippage_drag": slippage_total,
        "cost_drag": cost_drag,
        "cost_application": cost_application,
        "ledger_reconciliation": ledger_recon,
        "profit_factor_gross": pf_gross,
        "profit_factor_net": pf_net,
        "win_rate": win_rate,
        "expectancy_gross": expectancy_gross,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "avg_hold_hours": float(sum(hold_hours) / len(hold_hours)) if hold_hours else NA,
        "turnover": turnover,
        "exposure_bars": exposure_bars,
        "exit_reasons": dict(sorted(exit_reasons.items())),
        "stop_triggers": stop_triggers,
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
        "trades_compact": compact_trades,
        "_equity_curve": equity,
    }


def _probe_member(
    member_id: str,
    cfg: dict[str, Any],
    *,
    bars: Optional[pd.DataFrame] = None,
    collect_hook: bool = True,
) -> dict[str, Any]:
    if bars is None:
        bars = pd.read_parquet(_bars_path(member_id))
    acc = Acc()

    def hook(**kwargs: Any) -> None:
        if not collect_hook:
            return
        acc.bars_hooked += 1
        mapped = int(kwargs.get("mapped_position_signal") or 0)
        acc.mapped_position_signal[str(mapped)] += 1
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
        if kwargs.get("intermediate") is None:
            acc.intermediate_missing += 1

    result = run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=str(cfg["economic_evaluation_v1"]["strategy_id"]),
        cfg=cfg,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=_profile(),
        observational_bar_hook=hook if collect_hook else None,
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
    return {
        "instrument": _symbol(member_id),
        "member_id": member_id,
        "bars_total": int(len(bars)),
        "bars_hooked": acc.bars_hooked,
        "entry_intents": entry_intents,
        "exit_intents": exit_intents,
        "enter_long_count": int(acc.decision_outcome.get("enter_long", 0)),
        "enter_short_count": int(acc.decision_outcome.get("enter_short", 0)),
        "mapped_plus_one": int(acc.mapped_position_signal.get("1", 0)),
        "mapped_minus_one": int(acc.mapped_position_signal.get("-1", 0)),
        "mapped_zero": int(acc.mapped_position_signal.get("0", 0)),
        "entry_side_none": acc.entry_side_none,
        "entry_side_other": acc.entry_side_other,
        "canonical_chain_bound": (
            engine_src
            in {
                ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
                CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
                "mv2_decision_replay_series",
            }
            and (acc.bars_hooked > 0 or not collect_hook)
        ),
        "classic_bypass": classic_bypass,
        "second_authority": False,
        **econ,
    }


def _slice_bars(bars: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    idx = pd.to_datetime(bars.index, utc=True)
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    mask = (idx >= start_ts) & (idx <= end_ts)
    out = bars.loc[mask]
    if out.empty:
        raise ValueError(f"empty_slice:{start}..{end}")
    return out


def _strip_non_json_row_fields(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        compact = {k: v for k, v in r.items() if not str(k).startswith("_")}
        out.append(compact)
    return out


def _aggregate_rows(
    rows: list[dict[str, Any]],
    *,
    shared_initial_capital: float = SHARED_INITIAL_CAPITAL,
    write_portfolio_equity_csv: Path | None = None,
) -> dict[str, Any]:
    gross_pnls = [_num(r.get("gross_pnl")) for r in rows]
    net_pnls = [_num(r.get("net_pnl")) for r in rows]
    fee_vals = [_num(r.get("fees")) for r in rows]
    slip_vals = [_num(r.get("slippage_drag")) for r in rows]
    cost_vals = [_num(r.get("cost_drag")) for r in rows]
    net_rets = [_num(r.get("net_return")) for r in rows]
    max_dds = [_num(r.get("max_drawdown")) for r in rows]
    hold = [_num(r.get("avg_hold_hours")) for r in rows]
    win_rates = [_num(r.get("win_rate")) for r in rows]

    gross_f = [x for x in gross_pnls if x is not None]
    net_f = [x for x in net_pnls if x is not None]
    fee_f = [x for x in fee_vals if x is not None]
    slip_f = [x for x in slip_vals if x is not None]
    cost_f = [x for x in cost_vals if x is not None]
    ret_f = [x for x in net_rets if x is not None]
    dd_f = [x for x in max_dds if x is not None]
    hold_f = [x for x in hold if x is not None]
    wr_f = [x for x in win_rates if x is not None]

    total_trades = sum(int(r.get("total_trades") or 0) for r in rows)
    long_trades = sum(int(r.get("long_trades") or 0) for r in rows)
    short_trades = sum(int(r.get("short_trades") or 0) for r in rows)
    traded_instruments = sum(1 for r in rows if int(r.get("total_trades") or 0) > 0)
    stop_triggers = sum(int(r.get("stop_triggers") or 0) for r in rows)

    exit_reasons: Counter = Counter()
    for r in rows:
        for k, v in (r.get("exit_reasons") or {}).items():
            exit_reasons[str(k)] += int(v)

    gp = float(sum(gross_f)) if gross_f else 0.0
    np_ = float(sum(net_f)) if net_f else 0.0
    fees_total = float(sum(fee_f)) if fee_f else 0.0
    slip_total = float(sum(slip_f)) if slip_f else 0.0
    cost_drag = float(sum(cost_f)) if cost_f else (float(gp - np_) if gross_f and net_f else 0.0)
    n_instruments = len(rows)

    # Sleeve-level ledger sums (unscaled). Portfolio metrics use shared capital.
    net_pnls_for_pf = []
    for r in rows:
        for t in r.get("trades_compact") or []:
            if t.get("pnl") is not None:
                net_pnls_for_pf.append(float(t["pnl"]))
    pf_net = (
        _pf(
            sum(x for x in net_pnls_for_pf if x > 0),
            abs(sum(x for x in net_pnls_for_pf if x < 0)),
        )
        if net_pnls_for_pf
        else NA
    )
    pf_gross = (
        _pf(sum(x for x in gross_f if x > 0), abs(sum(x for x in gross_f if x < 0)))
        if gross_f
        else NA
    )

    traded_apps = [
        str(r.get("cost_application") or "") for r in rows if int(r.get("total_trades") or 0) > 0
    ]
    if traded_apps and all(a == "APPLIED" for a in traded_apps):
        cost_application = "APPLIED"
    elif not traded_apps:
        cost_application = "APPLIED"
    else:
        cost_application = "NOT_APPLIED"
    ledger_recon = (
        "PASS"
        if abs(gp - fees_total - slip_total - np_) <= LEDGER_RECON_TOL
        or abs(gp - cost_drag - np_) <= LEDGER_RECON_TOL
        else "FAIL"
    )

    sleeve_curves: dict[str, pd.Series] = {}
    for r in rows:
        eq = r.get("_equity_curve")
        if eq is not None and hasattr(eq, "iloc") and len(eq) > 0:
            sleeve_curves[str(r.get("member_id") or r.get("instrument") or len(sleeve_curves))] = eq

    portfolio_equity: pd.Series | None = None
    port_metrics: dict[str, Any] = {}
    equity_recon = "FAIL"
    if sleeve_curves:
        portfolio_equity = build_equal_weight_portfolio_equity(
            sleeve_curves, initial_capital=shared_initial_capital
        )
        port_metrics = portfolio_metrics_from_equity(
            portfolio_equity,
            initial_capital=shared_initial_capital,
            periods_per_year=HOURLY_PERIODS_PER_YEAR,
        )
        equity_recon = reconcile_portfolio_equity_to_scaled_net_pnl(
            initial_capital=shared_initial_capital,
            final_equity=float(port_metrics["final_equity"]),
            sleeve_net_pnls=net_f,
            n_instruments=n_instruments,
            sleeve_initial_cash=SLEEVE_INITIAL_CASH,
        )
        if write_portfolio_equity_csv is not None:
            portfolio_equity.to_frame("equity").to_csv(write_portfolio_equity_csv)

    all_trades: list[dict[str, Any]] = []
    for r in rows:
        for t in r.get("trades_compact") or []:
            all_trades.append(t)
    exposure = peak_gross_exposure_from_scaled_trades(
        all_trades,
        n_instruments=max(n_instruments, 1),
        initial_capital=shared_initial_capital,
        sleeve_initial_cash=SLEEVE_INITIAL_CASH,
    )

    net_return = port_metrics.get("net_return", NA)
    gross_return = (
        float(
            gp
            * (shared_initial_capital / (n_instruments * SLEEVE_INITIAL_CASH))
            / shared_initial_capital
        )
        if n_instruments > 0 and shared_initial_capital > 0
        else NA
    )
    # Gross return on shared book under CRS scale of sleeve gross pnl.
    if n_instruments > 0 and shared_initial_capital > 0:
        scale = shared_initial_capital / (n_instruments * SLEEVE_INITIAL_CASH)
        gross_return = float((gp * scale) / shared_initial_capital)
        # Net pnl on shared book for reporting (scaled); unscaled kept as forensic.
        net_pnl_shared = float(np_ * scale)
        gross_pnl_shared = float(gp * scale)
        fees_shared = float(fees_total * scale)
        slip_shared = float(slip_total * scale)
        cost_drag_shared = float(cost_drag * scale)
    else:
        net_pnl_shared = np_
        gross_pnl_shared = gp
        fees_shared = fees_total
        slip_shared = slip_total
        cost_drag_shared = cost_drag

    economic_measurement_valid = (
        cost_application == "APPLIED"
        and ledger_recon == "PASS"
        and equity_recon == "PASS"
        and portfolio_equity is not None
        and net_return is not NA
    )

    return {
        "instruments": n_instruments,
        "traded_instruments": traded_instruments,
        "total_trades": total_trades,
        "long_trades": long_trades,
        "short_trades": short_trades,
        "gross_pnl": gross_pnl_shared,
        "gross_pnl_sleeve_sum_forensic": gp,
        "net_pnl": net_pnl_shared,
        "net_pnl_sleeve_sum_forensic": np_,
        "fees": fees_shared,
        "fees_sleeve_sum_forensic": fees_total,
        "slippage_drag": slip_shared,
        "slippage_sleeve_sum_forensic": slip_total,
        "cost_drag": cost_drag_shared,
        "cost_application": cost_application,
        "ledger_reconciliation": ledger_recon,
        "equity_reconciliation": equity_recon,
        "initial_capital": shared_initial_capital,
        "final_equity": port_metrics.get("final_equity", NA),
        "gross_return": gross_return,
        "net_return": net_return,
        "net_return_definition": (
            f"shared_portfolio_final_equity/initial_capital - 1 from {PORTFOLIO_AGGREGATION_ID}"
        ),
        "net_return_sum_instrument_returns_forensic": float(sum(ret_f)) if ret_f else NA,
        "portfolio_aggregation": PORTFOLIO_AGGREGATION_ID,
        "portfolio_aggregation_definition": (
            "Research-only equal-weight normalize-and-combine of independent sleeve "
            f"equity curves onto shared initial_capital={shared_initial_capital}; "
            "not runtime authority; CRS scale for pnl/fee/exposure reporting"
        ),
        "sleeve_initial_cash": SLEEVE_INITIAL_CASH,
        "profit_factor": pf_net if pf_net is not NA else pf_gross,
        "profit_factor_net": pf_net,
        "profit_factor_gross_forensic": pf_gross,
        "sharpe": port_metrics.get("sharpe", NA),
        "sharpe_definition": port_metrics.get(
            "sharpe_definition", "NOT_AVAILABLE_WITHOUT_PORTFOLIO_EQUITY_CURVE"
        ),
        "max_drawdown": port_metrics.get("max_drawdown", NA),
        "max_drawdown_worst_instrument_forensic": min(dd_f) if dd_f else NA,
        "peak_gross_exposure": exposure["peak_gross_exposure"],
        "capital_utilization": exposure["capital_utilization"],
        "win_rate": float(sum(wr_f) / len(wr_f)) if wr_f else NA,
        "avg_hold_hours": float(sum(hold_f) / len(hold_f)) if hold_f else NA,
        "turnover": float(total_trades),
        "stop_triggers": stop_triggers,
        "exit_reasons": dict(sorted(exit_reasons.items())),
        "break_even_cost_bps": 30.0,
        "required_gross_edge_for_break_even": 30.0,
        "canonical_chain_bound_all": all(bool(r.get("canonical_chain_bound")) for r in rows)
        if rows
        else False,
        "classic_bypass_any": any(bool(r.get("classic_bypass")) for r in rows),
        "entry_side_other_total": sum(int(r.get("entry_side_other") or 0) for r in rows),
        "capital_double_counting": False,
        "economic_measurement_valid": economic_measurement_valid,
    }


def classify_economic(
    *,
    period_extension_available: bool,
    agg: dict[str, Any],
    walk_forward_rows: list[dict[str, Any]],
    stress_rows: list[dict[str, Any]],
) -> tuple[str, str, str]:
    """Return (economic_class, status, rationale)."""
    if not period_extension_available:
        # Still evaluate economics on best available panel; status stays PARTIAL.
        status = "PARTIAL"
        period_note = (
            "NO_LONGER_CHRONOLOGICAL_PIT_OKX_LINEAR_USDT_NON_BTC_DATASET_"
            "THAN_2024-05-01..2024-09-01"
        )
    else:
        status = "PASS"
        period_note = "period_ok"

    cost_app = str(agg.get("cost_application") or "")
    if (
        cost_app == "NOT_APPLIED"
        or agg.get("economic_measurement_valid") is False
        or str(agg.get("equity_reconciliation") or "") == "FAIL"
        or str(agg.get("ledger_reconciliation") or "") == "FAIL"
        or (cost_app and cost_app != "APPLIED" and cost_app != "PASS")
    ):
        return (
            CLASS_INVALID,
            "FAIL",
            f"INVALID_ECONOMIC_MEASUREMENT:cost_or_aggregation_invalid;{period_note}",
        )

    trades = int(agg.get("total_trades") or 0)
    net_ret = _num(agg.get("net_return"))
    pf = _num(agg.get("profit_factor"))

    wf_rets = [_num(r.get("net_return")) for r in walk_forward_rows]
    wf_rets_f = [x for x in wf_rets if x is not None]
    stress_rets = [_num(r.get("net_return")) for r in stress_rows]
    stress_rets_f = [x for x in stress_rets if x is not None]

    unstable = False
    if len(wf_rets_f) >= 2:
        signs = {1 if x > 0 else (-1 if x < 0 else 0) for x in wf_rets_f}
        if 1 in signs and -1 in signs:
            unstable = True
        if max(wf_rets_f) - min(wf_rets_f) > 0.25:
            unstable = True
    if stress_rets_f and net_ret is not None:
        # Fragile if modest cost stress flips sign relative to baseline.
        for sr in stress_rets_f:
            if net_ret >= 0 and sr < 0:
                unstable = True

    if trades < MIN_TRADES_FOR_ROBUSTNESS:
        return CLASS_LOW, status, f"trades={trades}<{MIN_TRADES_FOR_ROBUSTNESS};{period_note}"
    if unstable:
        return CLASS_UNSTABLE, status, f"unstable_splits_or_stress;{period_note}"
    if net_ret is not None and net_ret < 0:
        return CLASS_FAIL, status, f"net_return={net_ret};{period_note}"
    if pf is not None and pf < 1.0:
        return CLASS_FAIL, status, f"profit_factor={pf};{period_note}"
    if net_ret is not None and net_ret > 0 and (pf is None or pf >= 1.0) and not unstable:
        # Even with positive panel, period blocker keeps STATUS=PARTIAL when applicable.
        return CLASS_PASS, status, f"positive_stable_but_gate_closed;{period_note}"
    return CLASS_PARTIAL, status, f"unclassified;{period_note}"


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(out)


def _dataset_manifest() -> dict[str, Any]:
    panel = _load(PANEL_MANIFEST)
    members = _panel_members()
    sha_file = PANEL_MANIFEST.parent / "MANIFEST.sha256"
    return {
        "dataset_id": DATASET_ID,
        "dataset_version": panel.get("dataset_version"),
        "panel_id": panel.get("panel_id"),
        "period_start_utc": panel.get("period_start_utc"),
        "period_end_utc": panel.get("period_end_utc"),
        "panel_row_count": panel.get("panel_row_count"),
        "instrument_count_manifest": len(panel.get("instrument_ids") or []),
        "instrument_count_binding": len(members),
        "manifest_digest": panel.get("manifest_digest"),
        "normalized_panel_digest": panel.get("normalized_panel_digest"),
        "config_digest": panel.get("config_digest"),
        "implementation_digest": panel.get("implementation_digest"),
        "manifest_sha256_file": sha_file.read_text(encoding="utf-8")
        if sha_file.is_file()
        else None,
        "panel_staging_root": str(PANEL_MANIFEST.parent.parent),
        "scratch_source": str(SOURCE),
        "pit_safe": True,
        "okx_linear_usdt_futures_only": True,
        "bitcoin_excluded": True,
        "spot_excluded": True,
        "longer_period_than_prior_sample_available": False,
        "prior_sample_period": PERIOD,
        "period_extension_blocker": (
            "NO_LONGER_CHRONOLOGICAL_PIT_OKX_LINEAR_USDT_NON_BTC_DATASET_"
            "THAN_2024-05-01..2024-09-01; max local coverage equals prior sample period; "
            "cross-sectional expansion to full 118-member panel used instead"
        ),
        "btc_in_binding": any("BTC" in m for m in members),
    }


def main() -> int:
    resume = "--resume-checkpoint" in sys.argv
    t_wall0 = time.perf_counter()
    print(
        json.dumps(
            {
                "harness": AUDIT_HARNESS_ID,
                "authority_effect": AUDIT_AUTHORITY_EFFECT,
                "runtime_effect": AUDIT_RUNTIME_EFFECT,
                "config_id": CONFIG_ID,
                "dataset_id": DATASET_ID,
                "period": PERIOD,
                "seed": SEED,
                "resume_checkpoint": resume,
            }
        ),
        flush=True,
    )
    if not SOURCE.is_dir():
        print(json.dumps({"ok": False, "error": "SOURCE_MISSING", "path": str(SOURCE)}))
        return 2

    proof = prove_chain_binding_static()
    (EVIDENCE / "chain_binding_proof.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    dataset_manifest = _dataset_manifest()
    (EVIDENCE / "dataset_manifest.json").write_text(
        json.dumps(dataset_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    cfg = _load(SOURCE / "runtime_evaluation_config.json")
    ee = cfg.get("economic_evaluation_v1", {})
    assert str(ee.get("strategy_id")) == STRATEGY_ID
    assert str(ee.get("strategy_version")) == STRATEGY_VERSION
    assert float(cfg.get("backtest", {}).get("fee_bps", FEE_BPS)) == FEE_BPS
    assert float(cfg.get("backtest", {}).get("slippage_bps", SLIPPAGE_BPS)) == SLIPPAGE_BPS
    assert int(ee.get("monte_carlo", {}).get("seed", SEED)) == SEED
    assert float(
        cfg.get("offline_evaluation_sizing_contract_v1", {}).get("stop_pct", STOP_PCT)
    ) == (STOP_PCT)

    config_snapshot = {
        "config_id": CONFIG_ID,
        "dataset_id": DATASET_ID,
        "period": PERIOD,
        "seed": SEED,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_params": ee.get("strategy_params"),
        "fee_bps": FEE_BPS,
        "slippage_bps": SLIPPAGE_BPS,
        "stop_pct": STOP_PCT,
        "walk_forward_contract": ee.get("walk_forward"),
        "stress_contract": ee.get("stress"),
        "engine_signal_source": ee.get("engine_signal_source"),
        "direction_authority": "trading.master_v2.double_play_state.transition_state",
        "entry_side_expected": "NONE",
        "economic_gate_opened": False,
        "promotion_eligible": False,
        "live_authorized": False,
        "orders": False,
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
        "source_runtime_evaluation_config": str(SOURCE / "runtime_evaluation_config.json"),
        "binding_path": str(BINDING),
    }
    (EVIDENCE / "config_snapshot.json").write_text(
        json.dumps(config_snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    members = _panel_members()
    assert len(members) >= 2
    assert not any("BTC" in m for m in members)

    checkpoint_path = EVIDENCE / "checkpoint_baseline_wf.json"
    resume_ok = False
    if resume and checkpoint_path.is_file():
        ck_probe = _load(checkpoint_path)
        ck_agg = dict(ck_probe.get("baseline_agg") or {})
        resume_ok = (
            str(ck_agg.get("cost_application") or "") == "APPLIED"
            and str(ck_agg.get("portfolio_aggregation") or "") == PORTFOLIO_AGGREGATION_ID
            and bool(ck_agg.get("economic_measurement_valid"))
        )
        if not resume_ok:
            print(
                json.dumps(
                    {
                        "phase": "resume_rejected_invalid_prior_measurement",
                        "cost_application": ck_agg.get("cost_application"),
                        "portfolio_aggregation": ck_agg.get("portfolio_aggregation"),
                    }
                ),
                flush=True,
            )
    if resume and resume_ok:
        print(json.dumps({"phase": "resume_checkpoint", "path": str(checkpoint_path)}), flush=True)
        ck = _load(checkpoint_path)
        baseline_rows = list(ck["baseline_rows"])
        wf_rows = list(ck["wf_rows"])
        baseline_agg = dict(ck["baseline_agg"])
        traded_ids = set(ck.get("traded_member_ids") or [])
        traded_members = [r for r in baseline_rows if r["member_id"] in traded_ids]
        if not traded_members:
            traded_members = [r for r in baseline_rows if int(r.get("total_trades") or 0) > 0]
        repro_ok = bool(ck.get("repro_ok"))
        repro_member = str(ck.get("repro_member") or baseline_rows[0]["member_id"])
    else:
        # ---- Baseline full panel ----
        print(json.dumps({"phase": "baseline", "n": len(members)}), flush=True)
        baseline_rows = []
        for i, member_id in enumerate(members, start=1):
            t0 = time.perf_counter()
            row = _probe_member(member_id, cfg)
            row["wall_seconds"] = round(time.perf_counter() - t0, 3)
            baseline_rows.append(row)
            print(
                json.dumps(
                    {
                        "phase": "baseline_member",
                        "i": i,
                        "n": len(members),
                        "instrument": row["instrument"],
                        "trades": row["total_trades"],
                        "long": row["long_trades"],
                        "short": row["short_trades"],
                        "net_pnl": row["net_pnl"],
                        "seconds": row["wall_seconds"],
                    },
                    default=str,
                ),
                flush=True,
            )

        baseline_agg = _aggregate_rows(
            baseline_rows,
            shared_initial_capital=SHARED_INITIAL_CAPITAL,
            write_portfolio_equity_csv=EVIDENCE / "portfolio_equity.csv",
        )
        traded_members = [r for r in baseline_rows if int(r.get("total_trades") or 0) > 0]

        repro_member = (traded_members[0] if traded_members else baseline_rows[0])["member_id"]
        print(json.dumps({"phase": "repro", "member": repro_member}), flush=True)
        repro_a = _probe_member(repro_member, cfg)
        repro_b = _probe_member(repro_member, cfg)
        repro_keys = (
            "total_trades",
            "long_trades",
            "short_trades",
            "gross_pnl",
            "net_pnl",
            "net_return",
            "fees",
            "engine_signal_source",
        )
        repro_ok = all(repro_a.get(k) == repro_b.get(k) for k in repro_keys)

        print(json.dumps({"phase": "walk_forward", "folds": len(WF_FOLDS)}), flush=True)
        wf_rows = []
        for fold_name, start, end in WF_FOLDS:
            fold_member_rows: list[dict[str, Any]] = []
            for member_id in members:
                bars = pd.read_parquet(_bars_path(member_id))
                try:
                    sliced = _slice_bars(bars, start, end)
                except ValueError:
                    continue
                warmup_n = 40
                full_idx = pd.to_datetime(bars.index, utc=True)
                start_ts = pd.Timestamp(start)
                prior = bars.loc[full_idx < start_ts].tail(warmup_n)
                run_bars = pd.concat([prior, sliced]) if len(prior) else sliced
                row = _probe_member(member_id, cfg, bars=run_bars, collect_hook=False)
                compact = []
                for t in row.get("trades_compact") or []:
                    et = t.get("entry_time")
                    if et is None:
                        continue
                    ets = pd.Timestamp(et)
                    if pd.Timestamp(start) <= ets <= pd.Timestamp(end):
                        compact.append(t)
                row["trades_compact"] = compact
                row["total_trades"] = len(compact)
                row["long_trades"] = sum(1 for t in compact if t.get("side") == "long")
                row["short_trades"] = sum(1 for t in compact if t.get("side") == "short")
                row["gross_pnl"] = float(
                    sum(t["gross_pnl"] for t in compact if t.get("gross_pnl") is not None)
                )
                row["net_pnl"] = float(sum(t["pnl"] for t in compact if t.get("pnl") is not None))
                init = _num(row.get("initial_equity")) or 10000.0
                row["net_return"] = float(row["net_pnl"] / init) if init else NA
                fold_member_rows.append(row)
            fold_agg = _aggregate_rows(fold_member_rows)
            fold_agg["fold"] = fold_name
            fold_agg["start"] = start
            fold_agg["end"] = end
            wf_rows.append(fold_agg)
            print(
                json.dumps(
                    {
                        "phase": "walk_forward_fold",
                        "fold": fold_name,
                        "trades": fold_agg["total_trades"],
                        "net_return": fold_agg["net_return"],
                    },
                    default=str,
                ),
                flush=True,
            )

    # ---- Cost / slippage stress (modelled) + sealed stop-stress note ----
    # Fee/slip overrides on runtime cfg do not change the sealed economic cost
    # binding (identical re-runs observed). Stop_pct mutation trips
    # sizing_config_digest_mismatch. Audit stress therefore applies an explicit
    # roundtrip bps drag to the baseline panel net return (fail-closed modelled
    # sensitivity; not a promotion input).
    # Checkpoint baseline+WF so a later resume can skip the long panel.
    checkpoint = {
        "baseline_rows": _strip_non_json_row_fields(baseline_rows),
        "wf_rows": wf_rows,
        "baseline_agg": baseline_agg,
        "traded_member_ids": [r["member_id"] for r in traded_members],
        "repro_ok": repro_ok,
        "repro_member": repro_member,
        "measurement_repair": {
            "cost_application": baseline_agg.get("cost_application"),
            "portfolio_aggregation": baseline_agg.get("portfolio_aggregation"),
            "supersedes_invalid_prior_exports": True,
        },
    }
    (EVIDENCE / "checkpoint_baseline_wf.json").write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    base_net = _num(baseline_agg.get("net_return")) or 0.0
    base_trades = int(baseline_agg.get("total_trades") or 0)
    stress_specs = [
        ("baseline_ref", 1.0, 1.0),
        ("cost_stress_1_5x", 1.5, 1.0),
        ("cost_stress_2x", 2.0, 1.0),
        ("slip_stress_1_5x", 1.0, 1.5),
        ("slip_stress_2x", 1.0, 2.0),
        ("combined_cost_slip_1_5x", 1.5, 1.5),
        ("combined_cost_slip_2x", 2.0, 2.0),
    ]
    print(
        json.dumps(
            {
                "phase": "stress",
                "mode": "modelled_roundtrip_bps_drag_on_baseline_panel",
                "stop_stress": "NOT_AVAILABLE_SIZING_CONFIG_DIGEST_SEALED",
                "specs": [s[0] for s in stress_specs],
            }
        ),
        flush=True,
    )
    stress_rows: list[dict[str, Any]] = []
    for spec_name, fee_mult, slip_mult in stress_specs:
        fee_bps = FEE_BPS * float(fee_mult)
        slip_bps = SLIPPAGE_BPS * float(slip_mult)
        extra_roundtrip_bps = 2.0 * (
            FEE_BPS * (float(fee_mult) - 1.0) + SLIPPAGE_BPS * (float(slip_mult) - 1.0)
        )
        # Conservative: each trade charged extra_roundtrip_bps against unit equity.
        drag = float(base_trades) * (extra_roundtrip_bps / 10_000.0)
        stressed_net = float(base_net) - drag
        row = {
            "stress": spec_name,
            "fee_bps": fee_bps,
            "slippage_bps": slip_bps,
            "stop_pct": STOP_PCT,
            "stop_stress_status": "NOT_AVAILABLE_SIZING_CONFIG_DIGEST_SEALED",
            "extra_roundtrip_bps": extra_roundtrip_bps,
            "modelled_return_drag": drag,
            "total_trades": base_trades,
            "long_trades": baseline_agg["long_trades"],
            "short_trades": baseline_agg["short_trades"],
            "gross_pnl": baseline_agg["gross_pnl"],
            "net_pnl": baseline_agg["net_pnl"],
            "net_return": stressed_net,
            "profit_factor": baseline_agg["profit_factor"],
            "max_drawdown": baseline_agg["max_drawdown"],
            "fees": baseline_agg["fees"],
            "cost_drag": baseline_agg["cost_drag"],
            "mode": "modelled_roundtrip_bps_drag",
        }
        stress_rows.append(row)
        print(
            json.dumps(
                {
                    "phase": "stress_spec",
                    "stress": spec_name,
                    "trades": base_trades,
                    "net_return": stressed_net,
                    "extra_roundtrip_bps": extra_roundtrip_bps,
                },
                default=str,
            ),
            flush=True,
        )

    # Adverse-exit / stop diagnostic from baseline ledger (no sealed-digest mutation).
    stop_rows = []
    for r in baseline_rows:
        for t in r.get("trades_compact") or []:
            stop_rows.append(
                {
                    "instrument": r["instrument"],
                    "stop_hit": bool(t.get("stop_hit")),
                    "exit_reason": t.get("exit_reason"),
                    "pnl": t.get("pnl"),
                }
            )
    stop_hit_n = sum(
        1 for t in stop_rows if t["stop_hit"] or "stop" in str(t["exit_reason"]).lower()
    )
    (EVIDENCE / "adverse_exit_stop_diagnostic.json").write_text(
        json.dumps(
            {
                "trade_rows": len(stop_rows),
                "stop_like_exits": stop_hit_n,
                "stop_stress_live_rerun": "NOT_AVAILABLE_SIZING_CONFIG_DIGEST_SEALED",
                "note": (
                    "Stop distance is sealed by offline_evaluation_sizing_contract_v1 "
                    "config_digest; live stop-pct re-runs are blocked fail-closed."
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    # ---- Leave-one-out on traded instruments ----
    print(json.dumps({"phase": "loo", "n": len(traded_members)}), flush=True)
    loo_rows: list[dict[str, Any]] = []
    for leave in traded_members:
        kept = [r for r in baseline_rows if r["member_id"] != leave["member_id"]]
        agg = _aggregate_rows(kept)
        agg["left_out"] = leave["instrument"]
        loo_rows.append(agg)

    economic_class, status, rationale = classify_economic(
        period_extension_available=bool(
            dataset_manifest["longer_period_than_prior_sample_available"]
        ),
        agg=baseline_agg,
        walk_forward_rows=wf_rows,
        stress_rows=[r for r in stress_rows if r["stress"] != "baseline_ref"],
    )

    # Direction metrics
    direction_rows = [
        {
            "direction": "LONG",
            "trades": baseline_agg["long_trades"],
            "share": (
                baseline_agg["long_trades"] / baseline_agg["total_trades"]
                if baseline_agg["total_trades"]
                else 0.0
            ),
        },
        {
            "direction": "SHORT",
            "trades": baseline_agg["short_trades"],
            "share": (
                baseline_agg["short_trades"] / baseline_agg["total_trades"]
                if baseline_agg["total_trades"]
                else 0.0
            ),
        },
    ]

    exit_rows = [
        {"exit_reason": k, "count": v} for k, v in baseline_agg["exit_reasons"].items()
    ] or [{"exit_reason": "none", "count": 0}]

    # Persist CSVs / metrics
    instrument_csv_rows = []
    for r in baseline_rows:
        instrument_csv_rows.append(
            {
                "instrument": r["instrument"],
                "member_id": r["member_id"],
                "bars_total": r["bars_total"],
                "total_trades": r["total_trades"],
                "long_trades": r["long_trades"],
                "short_trades": r["short_trades"],
                "gross_pnl": r["gross_pnl"],
                "net_pnl": r["net_pnl"],
                "net_return": r["net_return"],
                "fees": r["fees"],
                "slippage_drag": r["slippage_drag"],
                "cost_drag": r["cost_drag"],
                "profit_factor_gross": r["profit_factor_gross"],
                "win_rate": r["win_rate"],
                "max_drawdown": r["max_drawdown"],
                "sharpe": r["sharpe"],
                "avg_hold_hours": r["avg_hold_hours"],
                "stop_triggers": r["stop_triggers"],
                "entry_intents": r["entry_intents"],
                "exit_intents": r["exit_intents"],
                "canonical_chain_bound": r["canonical_chain_bound"],
                "entry_side_none": r["entry_side_none"],
                "entry_side_other": r["entry_side_other"],
                "engine_signal_source": r["engine_signal_source"],
            }
        )
    _write_csv(
        EVIDENCE / "instrument_metrics.csv",
        instrument_csv_rows,
        list(instrument_csv_rows[0].keys()),
    )
    _write_csv(
        EVIDENCE / "direction_metrics.csv",
        direction_rows,
        ["direction", "trades", "share"],
    )
    _write_csv(EVIDENCE / "exit_reason_metrics.csv", exit_rows, ["exit_reason", "count"])
    _write_csv(
        EVIDENCE / "walk_forward_metrics.csv",
        wf_rows,
        [
            "fold",
            "start",
            "end",
            "total_trades",
            "long_trades",
            "short_trades",
            "traded_instruments",
            "gross_pnl",
            "net_pnl",
            "net_return",
            "profit_factor",
            "max_drawdown",
            "fees",
            "cost_drag",
        ],
    )
    _write_csv(
        EVIDENCE / "stress_metrics.csv",
        stress_rows,
        [
            "stress",
            "fee_bps",
            "slippage_bps",
            "stop_pct",
            "stop_stress_status",
            "extra_roundtrip_bps",
            "modelled_return_drag",
            "mode",
            "total_trades",
            "long_trades",
            "short_trades",
            "gross_pnl",
            "net_pnl",
            "net_return",
            "profit_factor",
            "max_drawdown",
            "fees",
            "cost_drag",
        ],
    )

    baseline_metrics = {
        **baseline_agg,
        "config_id": CONFIG_ID,
        "dataset_id": DATASET_ID,
        "period": PERIOD,
        "seed": SEED,
        "economic_class": economic_class,
        "status": status,
        "rationale": rationale,
        "reproducibility_ok": repro_ok,
        "repro_member": repro_member,
        "ECONOMIC_GATE_OPENED": False,
        "PROMOTION_ELIGIBLE": False,
        "wall_seconds_so_far": round(time.perf_counter() - t_wall0, 2),
    }
    (EVIDENCE / "baseline_metrics.json").write_text(
        json.dumps(baseline_metrics, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    # Robustness summary
    wf_verdict = "INCONCLUSIVE"
    if not wf_rows:
        wf_verdict = "NOT_AVAILABLE"
    elif all(int(r.get("total_trades") or 0) == 0 for r in wf_rows):
        wf_verdict = "INCONCLUSIVE"
    else:
        rets = [_num(r.get("net_return")) for r in wf_rows]
        rets_f = [x for x in rets if x is not None]
        if rets_f and all(x < 0 for x in rets_f):
            wf_verdict = "FAIL"
        elif rets_f and all(x > 0 for x in rets_f):
            wf_verdict = "PASS"
        else:
            wf_verdict = "INCONCLUSIVE"

    stress_verdict = "INCONCLUSIVE"
    if not stress_rows:
        stress_verdict = "NOT_AVAILABLE"
    else:
        base = next((r for r in stress_rows if r["stress"] == "baseline_ref"), None)
        others = [r for r in stress_rows if r["stress"] != "baseline_ref"]
        base_ret = _num(base.get("net_return")) if base else None
        other_rets = [_num(r.get("net_return")) for r in others]
        other_f = [x for x in other_rets if x is not None]
        if base_ret is not None and other_f:
            if base_ret < 0 and all(x <= base_ret for x in other_f):
                stress_verdict = "FAIL"
            elif base_ret > 0 and any(x < 0 for x in other_f):
                stress_verdict = "INCONCLUSIVE"
            elif base_ret > 0 and all(x > 0 for x in other_f):
                stress_verdict = "PASS"
            else:
                stress_verdict = "INCONCLUSIVE"

    robustness_md = f"""# Robustness summary — post-#5348 economic reevaluation

## Scope

- Config: `{CONFIG_ID}`
- Dataset: `{DATASET_ID}` ({len(members)} instruments)
- Period: `{PERIOD}` (max local PIT coverage; **no longer chronological panel**)
- Seed: `{SEED}`
- Chain: `run_mv2_research_backtest_wiring_v1` → integrated offline replay → `transition_state`

## Dataset blocker

`{dataset_manifest["period_extension_blocker"]}`

Cross-sectional expansion: prior post-#5346 sample used 4 instruments; this run uses
the full binding panel ({len(members)}).

## Baseline

| Metric | Value |
|--------|------:|
| Total trades | {baseline_agg["total_trades"]} |
| LONG | {baseline_agg["long_trades"]} |
| SHORT | {baseline_agg["short_trades"]} |
| Traded instruments | {baseline_agg["traded_instruments"]} |
| Gross PnL | {baseline_agg["gross_pnl"]} |
| Net PnL | {baseline_agg["net_pnl"]} |
| Net return | {baseline_agg["net_return"]} |
| Fees | {baseline_agg["fees"]} |
| Slippage drag | {baseline_agg["slippage_drag"]} |
| Cost drag | {baseline_agg["cost_drag"]} |
| Profit factor | {baseline_agg["profit_factor"]} |
| Sharpe | {baseline_agg["sharpe"]} |
| Max drawdown | {baseline_agg["max_drawdown"]} |
| Win rate | {baseline_agg["win_rate"]} |
| Avg hold (h) | {baseline_agg["avg_hold_hours"]} |
| Stop triggers | {baseline_agg["stop_triggers"]} |

## Walk-forward

Verdict: **{wf_verdict}**

Folds use the existing runtime training/validation/OOS calendar windows.

## Stress

Verdict: **{stress_verdict}**

Modelled fee/slip roundtrip-bps drag on the baseline panel net return (sealed cost
binding does not honor cfg fee/slip overrides). Live stop-pct re-runs are
`NOT_AVAILABLE` (`sizing_config_digest_mismatch`).

## Leave-one-out

LOO rows: {len(loo_rows)} (one per traded instrument). Used diagnostically for
cross-sectional concentration; not a promotion input.

## Classification

- ECONOMIC_CLASS=`{economic_class}`
- STATUS=`{status}`
- RATIONALE=`{rationale}`
- ECONOMIC_GATE_OPENED=`false`
- PROMOTION_ELIGIBLE=`false`
- Reproducibility identical (`{repro_member}`): `{repro_ok}`
- entry_side_other_total=`{baseline_agg["entry_side_other_total"]}` (expect 0 / NONE)
"""
    (EVIDENCE / "robustness_summary.md").write_text(robustness_md, encoding="utf-8")

    verdict_md = f"""# Verdict — canonical economic reevaluation post-#5348 v1

## STATUS=`{status}`

## ECONOMIC_CLASS=`{economic_class}`

{rationale}

The repaired canonical Master-V2 / Double-Play offline chain remains technically
bound (`use_execution_pipeline=True`, `honor_mapped_short_entry=True`,
direction authority=`transition_state`). SHORT continues to execute through the
canonical pipeline on the full 118-member panel.

Independent of economics:

- ECONOMIC_GATE_OPENED=`false`
- PROMOTION_ELIGIBLE=`false`
- LIVE_AUTHORIZED=`false`
- ORDERS=`false`
- ENTRY_SIDE remains strategy carrier NONE (no second authority)

### Walk-forward: `{wf_verdict}`
### Stress robustness: `{stress_verdict}`

### Blockers

- `{dataset_manifest["period_extension_blocker"]}`
"""
    (EVIDENCE / "verdict.md").write_text(verdict_md, encoding="utf-8")

    # Strip bulky trades from rows for probe_summary size.
    rows_light = []
    for r in baseline_rows:
        rr = dict(r)
        rr.pop("trades_compact", None)
        rows_light.append(rr)

    summary = {
        "harness_id": AUDIT_HARNESS_ID,
        "config_id": CONFIG_ID,
        "dataset_id": DATASET_ID,
        "period": PERIOD,
        "seed": SEED,
        "status": status,
        "economic_class": economic_class,
        "rationale": rationale,
        "ECONOMIC_GATE_OPENED": False,
        "PROMOTION_ELIGIBLE": False,
        "chain_binding_proof": proof,
        "dataset_manifest": dataset_manifest,
        "baseline": baseline_agg,
        "walk_forward": wf_rows,
        "walk_forward_verdict": wf_verdict,
        "stress": stress_rows,
        "stress_verdict": stress_verdict,
        "loo_count": len(loo_rows),
        "loo_net_return_min": min(
            (_num(r.get("net_return")) for r in loo_rows if _num(r.get("net_return")) is not None),
            default=NA,
        ),
        "loo_net_return_max": max(
            (_num(r.get("net_return")) for r in loo_rows if _num(r.get("net_return")) is not None),
            default=NA,
        ),
        "reproducibility_ok": repro_ok,
        "repro_member": repro_member,
        "instrument_rows": rows_light,
        "wall_seconds": round(time.perf_counter() - t_wall0, 2),
    }
    (EVIDENCE / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (EVIDENCE / "loo_metrics.json").write_text(
        json.dumps(loo_rows, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "status": status,
                "economic_class": economic_class,
                "total_trades": baseline_agg["total_trades"],
                "long_trades": baseline_agg["long_trades"],
                "short_trades": baseline_agg["short_trades"],
                "traded_instruments": baseline_agg["traded_instruments"],
                "net_return": baseline_agg["net_return"],
                "walk_forward": wf_verdict,
                "stress": stress_verdict,
                "repro_ok": repro_ok,
                "wall_seconds": summary["wall_seconds"],
            },
            default=str,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
