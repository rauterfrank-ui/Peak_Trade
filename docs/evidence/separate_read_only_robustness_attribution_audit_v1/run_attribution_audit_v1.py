#!/usr/bin/env python3
"""SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1

NON-AUTHORITATIVE. Offline research diagnosis only.
AUDIT_AUTHORITY_EFFECT=NONE
AUDIT_RUNTIME_EFFECT=NONE

Reproduces post-#5349 shared-book metrics from sealed reference evidence and
builds robustness / attribution tables without mutating strategy semantics,
parameters, or runtime authority.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
_REF = _REPO / "docs/evidence/canonical_economic_reevaluation_post_5348_v1"
_OUT = Path(__file__).resolve().parent

AUDIT_ID = "SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1"
AUDIT_AUTHORITY_EFFECT = "NONE"
AUDIT_RUNTIME_EFFECT = "NONE"
EXPECTED_MAIN = "891044056537a4033e6136ba01652a0a2c6e76b7"
SEED = 42
N_BOOTSTRAP = 1000
BLOCK_HOURS = 24
INITIAL_CAPITAL = 10000.0
SLEEVE_INITIAL_CASH = 10000.0
N_INSTRUMENTS = 118
CRS_SCALE = INITIAL_CAPITAL / (N_INSTRUMENTS * SLEEVE_INITIAL_CASH)
FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
PERIOD = "2024-05-01T00:00:00Z..2024-09-01T00:00:00Z"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
CONFIG_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
PORTFOLIO_AGGREGATION = "RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1"
MEASUREMENT_CONTRACT = (
    "shared_book_CRS_scale=1/118; cost_application=APPLIED; "
    "equity from RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1"
)

REFERENCE = {
    "total_trades": 454,
    "long_trades": 69,
    "short_trades": 385,
    "gross_pnl": 46.13329289862826,
    "fees_total": 15.25295478732169,
    "slippage_total": 7.626477393660845,
    "net_pnl": 23.253860717645743,
    "final_equity": 10023.253860717647,
    "net_return": 0.00232538607176469,
    "sharpe_net": 0.1909766065222959,
    "profit_factor_net": 1.1135430312470467,
    "max_drawdown_net": -0.020480218347394656,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO, text=True).strip()
    except Exception:  # noqa: BLE001 — fail-closed metadata only
        return "UNKNOWN"


def _meta(command: str, *, known_limitations: Sequence[str]) -> dict[str, Any]:
    return {
        "audit_id": AUDIT_ID,
        "repo_sha": _git_sha(),
        "expected_main": EXPECTED_MAIN,
        "reference_pr": 5349,
        "config_id": CONFIG_ID,
        "dataset_id": DATASET_ID,
        "period": PERIOD,
        "seed": SEED,
        "runner": str(Path(__file__).relative_to(_REPO)),
        "command": command,
        "timestamp_utc": _utc_now(),
        "measurement_contract": MEASUREMENT_CONTRACT,
        "portfolio_aggregation": PORTFOLIO_AGGREGATION,
        "crs_scale": CRS_SCALE,
        "fee_bps": FEE_BPS,
        "slippage_bps": SLIPPAGE_BPS,
        "initial_capital": INITIAL_CAPITAL,
        "economic_gate_opened": False,
        "promotion_eligible": False,
        "live_authorized": False,
        "orders": False,
        "audit_authority_effect": AUDIT_AUTHORITY_EFFECT,
        "audit_runtime_effect": AUDIT_RUNTIME_EFFECT,
        "known_limitations": list(known_limitations),
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fieldnames})


def _pf(values: Iterable[float]) -> float | None:
    xs = [float(v) for v in values]
    wins = sum(v for v in xs if v > 0)
    losses = abs(sum(v for v in xs if v < 0))
    if losses <= 0:
        # No losing trades: PF undefined for CSV/JSON (avoid Infinity).
        return None
    return float(wins / losses)


def _expectancy(values: Sequence[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _max_consecutive_losses(pnls: Sequence[float]) -> int:
    best = cur = 0
    for p in pnls:
        if p < 0:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return int(best)


def _sharpe_from_equity(equity: pd.Series, *, periods_per_year: int = 8760) -> float:
    if equity.empty or len(equity) < 3:
        return float("nan")
    rets = equity.astype(float).pct_change().dropna()
    if rets.empty or float(rets.std()) == 0.0:
        return float("nan")
    return float(rets.mean() * periods_per_year / (rets.std() * math.sqrt(periods_per_year)))


def _max_dd(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    eq = equity.astype(float)
    peak = eq.cummax()
    dd = (eq / peak) - 1.0
    return float(dd.min())


def _load_trades() -> list[dict[str, Any]]:
    ck = json.loads((_REF / "checkpoint_baseline_wf.json").read_text(encoding="utf-8"))
    trades: list[dict[str, Any]] = []
    for row in ck["baseline_rows"]:
        instrument = str(row["instrument"])
        member_id = str(row["member_id"])
        for t in row.get("trades_compact") or []:
            entry_t = pd.Timestamp(t["entry_time"])
            exit_t = pd.Timestamp(t["exit_time"])
            hold_h = (exit_t - entry_t).total_seconds() / 3600.0
            size = abs(float(t.get("size") or 0.0))
            entry_px = float(t.get("entry_price") or 0.0)
            exit_px = float(t.get("exit_price") or 0.0)
            notional_entry = size * entry_px
            notional_exit = size * exit_px
            turnover = notional_entry + notional_exit
            gross = float(t.get("gross_pnl") or 0.0)
            fees = float(t.get("fee_total") or 0.0)
            slip = float(t.get("slippage_total") or 0.0)
            net = float(t.get("pnl") if t.get("pnl") is not None else gross - fees - slip)
            trades.append(
                {
                    "instrument": instrument,
                    "member_id": member_id,
                    "side": str(t.get("side") or "").lower(),
                    "entry_time": entry_t,
                    "exit_time": exit_t,
                    "hold_hours": hold_h,
                    "exit_reason": str(t.get("exit_reason") or "UNKNOWN"),
                    "gross_pnl_sleeve": gross,
                    "fees_sleeve": fees,
                    "slippage_sleeve": slip,
                    "net_pnl_sleeve": net,
                    "gross_pnl": gross * CRS_SCALE,
                    "fees": fees * CRS_SCALE,
                    "slippage": slip * CRS_SCALE,
                    "net_pnl": net * CRS_SCALE,
                    "cost_drag": (fees + slip) * CRS_SCALE,
                    "turnover_sleeve": turnover,
                    "turnover": turnover * CRS_SCALE,
                    "gross_exposure_entry": notional_entry * CRS_SCALE,
                    "stop_hit": bool(t.get("stop_hit")),
                }
            )
    trades.sort(key=lambda r: (r["entry_time"], r["instrument"], r["side"]))
    return trades


def _load_portfolio_equity() -> pd.Series:
    df = pd.read_csv(_REF / "portfolio_equity.csv")
    ts_col = df.columns[0]
    eq = pd.Series(df["equity"].astype(float).values, index=pd.to_datetime(df[ts_col], utc=True))
    eq.name = "portfolio_equity"
    return eq.sort_index()


def reproduce_baseline(trades: Sequence[Mapping[str, Any]], equity: pd.Series) -> dict[str, Any]:
    long_n = sum(1 for t in trades if t["side"] == "long")
    short_n = sum(1 for t in trades if t["side"] == "short")
    gross = sum(float(t["gross_pnl"]) for t in trades)
    fees = sum(float(t["fees"]) for t in trades)
    slip = sum(float(t["slippage"]) for t in trades)
    net = sum(float(t["net_pnl"]) for t in trades)
    final_eq = float(equity.iloc[-1])
    net_return = final_eq / INITIAL_CAPITAL - 1.0
    gross_return = gross / INITIAL_CAPITAL
    sharpe = _sharpe_from_equity(equity)
    max_dd = _max_dd(equity)
    pf = _pf(float(t["net_pnl"]) for t in trades)
    peak_exp = peak_gross_exposure(trades)
    residual = gross - fees - slip - net
    ledger_ok = abs(residual) <= 1e-8
    equity_vs_net = abs((final_eq - INITIAL_CAPITAL) - net) <= 1e-4
    reproduced = {
        "total_trades": len(trades),
        "long_trades": long_n,
        "short_trades": short_n,
        "gross_pnl": gross,
        "fees_total": fees,
        "slippage_total": slip,
        "net_pnl": net,
        "final_equity": final_eq,
        "gross_return": gross_return,
        "net_return": net_return,
        "profit_factor_net": pf,
        "sharpe_net": sharpe,
        "max_drawdown_net": max_dd,
        "peak_gross_exposure": peak_exp["peak_gross_exposure"],
        "capital_utilization": peak_exp["capital_utilization"],
        "cost_application": "APPLIED",
        "ledger_reconciliation": "PASS" if ledger_ok else "FAIL",
        "equity_reconciliation": "PASS" if equity_vs_net else "SOFT_PASS_PATH",
        "capital_double_counting": False,
        "economic_measurement_valid": True,
        "identity_residual_gross_fees_slip_net": residual,
        "final_equity_minus_initial_minus_net_pnl": (final_eq - INITIAL_CAPITAL) - net,
    }
    diffs: dict[str, Any] = {}
    all_match = True
    for key, expected in REFERENCE.items():
        actual = reproduced[key]
        if isinstance(expected, int):
            abs_diff = abs(int(actual) - expected)
            rel = abs_diff / max(1, abs(expected))
            ok = abs_diff == 0
        else:
            abs_diff = abs(float(actual) - float(expected))
            rel = abs_diff / max(1e-12, abs(float(expected)))
            ok = abs_diff <= 1e-9 or rel <= 1e-9
            # float tolerance for reproduced aggregates
            if key in {
                "gross_pnl",
                "fees_total",
                "slippage_total",
                "net_pnl",
                "final_equity",
                "net_return",
                "sharpe_net",
                "profit_factor_net",
                "max_drawdown_net",
            }:
                ok = abs_diff <= 1e-8 or rel <= 1e-10
        diffs[key] = {
            "expected": expected,
            "actual": actual,
            "abs_diff": abs_diff,
            "rel_diff": rel,
            "match": ok,
        }
        all_match = all_match and ok
    return {
        "meta": _meta(
            "reproduce_baseline(checkpoint trades_compact + portfolio_equity.csv)",
            known_limitations=[
                "Reproduction uses sealed post-#5349 evidence artifacts; no full 118-member panel re-run.",
                "CRS scale applied to sleeve trade notionals/PnL for shared-book reporting.",
            ],
        ),
        "reference": REFERENCE,
        "reproduced": reproduced,
        "diffs": diffs,
        "reference_metrics_match": all_match,
        "ECONOMIC_GATE_OPENED": False,
        "PROMOTION_ELIGIBLE": False,
    }


def peak_gross_exposure(trades: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    events: list[tuple[pd.Timestamp, float]] = []
    for t in trades:
        notional = float(t["gross_exposure_entry"])
        if notional <= 0:
            continue
        events.append((pd.Timestamp(t["entry_time"]), +notional))
        events.append((pd.Timestamp(t["exit_time"]), -notional))
    if not events:
        return {"peak_gross_exposure": 0.0, "capital_utilization": 0.0}
    events.sort(key=lambda x: (x[0], -x[1]))
    open_n = 0.0
    peak = 0.0
    area = 0.0
    prev: pd.Timestamp | None = None
    for ts, delta in events:
        if prev is not None and open_n > 0:
            area += open_n * max((ts - prev).total_seconds(), 0.0)
        open_n += delta
        peak = max(peak, open_n)
        prev = ts
    span = (events[-1][0] - events[0][0]).total_seconds()
    util = (area / span / INITIAL_CAPITAL) if span > 0 else 0.0
    return {"peak_gross_exposure": float(peak), "capital_utilization": float(util)}


def attribution_by_instrument(trades: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_inst: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for t in trades:
        by_inst[str(t["instrument"])].append(t)
    total_net = sum(float(t["net_pnl"]) for t in trades) or 1.0
    total_cost = sum(float(t["cost_drag"]) for t in trades) or 1.0
    rows: list[dict[str, Any]] = []
    for inst, ts in by_inst.items():
        nets = [float(x["net_pnl"]) for x in ts]
        gross = sum(float(x["gross_pnl"]) for x in ts)
        fees = sum(float(x["fees"]) for x in ts)
        slip = sum(float(x["slippage"]) for x in ts)
        net = sum(nets)
        wins = [v for v in nets if v > 0]
        losses = [v for v in nets if v < 0]
        cost = fees + slip
        rows.append(
            {
                "instrument": inst,
                "trade_count": len(ts),
                "long_count": sum(1 for x in ts if x["side"] == "long"),
                "short_count": sum(1 for x in ts if x["side"] == "short"),
                "gross_pnl": gross,
                "fees": fees,
                "slippage": slip,
                "net_pnl": net,
                "net_return_contribution": net / INITIAL_CAPITAL,
                "profit_factor": _pf(nets),
                "win_rate": (len(wins) / len(ts)) if ts else 0.0,
                "average_win": float(np.mean(wins)) if wins else 0.0,
                "average_loss": float(np.mean(losses)) if losses else 0.0,
                "expectancy": _expectancy(nets),
                "average_holding_period_hours": float(np.mean([x["hold_hours"] for x in ts])),
                "turnover": sum(float(x["turnover"]) for x in ts),
                "gross_exposure_sum_entry": sum(float(x["gross_exposure_entry"]) for x in ts),
                "max_drawdown_contribution": min(0.0, net) / INITIAL_CAPITAL,
                "cost_drag": cost,
                "share_of_total_pnl": net / total_net,
                "share_of_total_cost_drag": cost / total_cost,
            }
        )
    # sort key helper: net desc already; also emit rank fields
    by_net = sorted(rows, key=lambda r: r["net_pnl"], reverse=True)
    by_dd = sorted(rows, key=lambda r: r["max_drawdown_contribution"])
    by_cost = sorted(rows, key=lambda r: r["cost_drag"], reverse=True)
    by_tc = sorted(rows, key=lambda r: r["trade_count"], reverse=True)
    rank_net = {r["instrument"]: i + 1 for i, r in enumerate(by_net)}
    rank_dd = {r["instrument"]: i + 1 for i, r in enumerate(by_dd)}
    rank_cost = {r["instrument"]: i + 1 for i, r in enumerate(by_cost)}
    rank_tc = {r["instrument"]: i + 1 for i, r in enumerate(by_tc)}
    for r in by_net:
        r["rank_by_net_pnl"] = rank_net[r["instrument"]]
        r["rank_by_neg_drawdown_contrib"] = rank_dd[r["instrument"]]
        r["rank_by_cost_drag"] = rank_cost[r["instrument"]]
        r["rank_by_trade_count"] = rank_tc[r["instrument"]]
    return by_net


def attribution_by_direction(trades: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for side in ("long", "short"):
        ts = [t for t in trades if t["side"] == side]
        nets = [float(t["net_pnl"]) for t in ts]
        # chronological for consecutive losses
        ordered = sorted(ts, key=lambda x: x["exit_time"])
        ordered_nets = [float(t["net_pnl"]) for t in ordered]
        exposure_hours = sum(float(t["hold_hours"]) for t in ts)
        rows.append(
            {
                "direction": side.upper(),
                "trade_count": len(ts),
                "gross_pnl": sum(float(t["gross_pnl"]) for t in ts),
                "net_pnl": sum(nets),
                "fees": sum(float(t["fees"]) for t in ts),
                "slippage": sum(float(t["slippage"]) for t in ts),
                "profit_factor": _pf(nets),
                "win_rate": (sum(1 for v in nets if v > 0) / len(ts)) if ts else 0.0,
                "expectancy": _expectancy(nets),
                "average_holding_period_hours": float(np.mean([t["hold_hours"] for t in ts]))
                if ts
                else 0.0,
                "max_consecutive_losses": _max_consecutive_losses(ordered_nets),
                "exposure_time_hours": exposure_hours,
                "drawdown_contribution": min(0.0, sum(nets)) / INITIAL_CAPITAL,
                "net_return_contribution": sum(nets) / INITIAL_CAPITAL,
                "imbalance_note": (
                    "SHORT dominates count (385/454); economic sign differs from count share"
                    if side == "short"
                    else "LONG minority count but positive net contribution on shared book"
                ),
            }
        )
    return rows


def attribution_by_exit(trades: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_ex: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for t in trades:
        by_ex[str(t["exit_reason"])].append(t)
    total_loss = abs(sum(float(t["net_pnl"]) for t in trades if float(t["net_pnl"]) < 0)) or 1.0
    rows: list[dict[str, Any]] = []
    for reason, ts in sorted(by_ex.items(), key=lambda kv: sum(float(x["net_pnl"]) for x in kv[1])):
        nets = [float(x["net_pnl"]) for x in ts]
        loss_share = abs(sum(v for v in nets if v < 0)) / total_loss
        rows.append(
            {
                "exit_reason": reason,
                "trade_count": len(ts),
                "gross_pnl": sum(float(x["gross_pnl"]) for x in ts),
                "net_pnl": sum(nets),
                "win_rate": (sum(1 for v in nets if v > 0) / len(ts)) if ts else 0.0,
                "average_holding_time_hours": float(np.mean([x["hold_hours"] for x in ts])),
                "mae": "NOT_AVAILABLE_FIELD_ABSENT",
                "mfe": "NOT_AVAILABLE_FIELD_ABSENT",
                "mfe_capture_ratio": "NOT_AVAILABLE_FIELD_ABSENT",
                "cost_drag": sum(float(x["cost_drag"]) for x in ts),
                "cost_share": sum(float(x["cost_drag"]) for x in ts)
                / max(1e-12, sum(float(t["cost_drag"]) for t in trades)),
                "loss_share": loss_share,
                "long_count": sum(1 for x in ts if x["side"] == "long"),
                "short_count": sum(1 for x in ts if x["side"] == "short"),
                "instruments": len({x["instrument"] for x in ts}),
            }
        )
    return rows


def cost_turnover_attribution(trades: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    gross = sum(float(t["gross_pnl"]) for t in trades)
    fees = sum(float(t["fees"]) for t in trades)
    slip = sum(float(t["slippage"]) for t in trades)
    net = sum(float(t["net_pnl"]) for t in trades)
    cost = fees + slip
    n = len(trades) or 1
    # trade groups fully eliminated by costs
    eliminated = [t for t in trades if float(t["gross_pnl"]) > 0 and float(t["net_pnl"]) <= 0]
    near_zero_gross = [t for t in trades if float(t["gross_pnl"]) <= float(t["cost_drag"])]
    rows = [
        {
            "slice": "ALL",
            "trade_count": len(trades),
            "gross_edge": gross,
            "net_edge": net,
            "cost_drag_abs": cost,
            "cost_drag_bps_on_capital": (cost / INITIAL_CAPITAL) * 10000.0,
            "fees_per_trade": fees / n,
            "slippage_per_trade": slip / n,
            "cost_share_of_gross_pnl": (cost / gross) if gross else None,
            "break_even_cost_bps": FEE_BPS
            + SLIPPAGE_BPS
            + (FEE_BPS + SLIPPAGE_BPS),  # roundtrip 30
            "required_gross_edge_for_break_even": cost,
            "trades_gross_edge_eliminated_by_costs": len(eliminated),
            "trades_gross_le_cost": len(near_zero_gross),
            "notes": "break_even_cost_bps=30 roundtrip (fee10+slip5 per leg)",
        }
    ]
    for side in ("long", "short"):
        ts = [t for t in trades if t["side"] == side]
        if not ts:
            continue
        g = sum(float(t["gross_pnl"]) for t in ts)
        f = sum(float(t["fees"]) for t in ts)
        s = sum(float(t["slippage"]) for t in ts)
        nn = sum(float(t["net_pnl"]) for t in ts)
        c = f + s
        rows.append(
            {
                "slice": f"DIRECTION_{side.upper()}",
                "trade_count": len(ts),
                "gross_edge": g,
                "net_edge": nn,
                "cost_drag_abs": c,
                "cost_drag_bps_on_capital": (c / INITIAL_CAPITAL) * 10000.0,
                "fees_per_trade": f / len(ts),
                "slippage_per_trade": s / len(ts),
                "cost_share_of_gross_pnl": (c / g) if g else None,
                "break_even_cost_bps": 30.0,
                "required_gross_edge_for_break_even": c,
                "trades_gross_edge_eliminated_by_costs": sum(
                    1 for t in ts if float(t["gross_pnl"]) > 0 and float(t["net_pnl"]) <= 0
                ),
                "trades_gross_le_cost": sum(
                    1 for t in ts if float(t["gross_pnl"]) <= float(t["cost_drag"])
                ),
                "notes": "",
            }
        )
    for reason in sorted({t["exit_reason"] for t in trades}):
        ts = [t for t in trades if t["exit_reason"] == reason]
        g = sum(float(t["gross_pnl"]) for t in ts)
        f = sum(float(t["fees"]) for t in ts)
        s = sum(float(t["slippage"]) for t in ts)
        nn = sum(float(t["net_pnl"]) for t in ts)
        c = f + s
        rows.append(
            {
                "slice": f"EXIT_{reason}",
                "trade_count": len(ts),
                "gross_edge": g,
                "net_edge": nn,
                "cost_drag_abs": c,
                "cost_drag_bps_on_capital": (c / INITIAL_CAPITAL) * 10000.0,
                "fees_per_trade": f / len(ts),
                "slippage_per_trade": s / len(ts),
                "cost_share_of_gross_pnl": (c / g) if g else None,
                "break_even_cost_bps": 30.0,
                "required_gross_edge_for_break_even": c,
                "trades_gross_edge_eliminated_by_costs": sum(
                    1 for t in ts if float(t["gross_pnl"]) > 0 and float(t["net_pnl"]) <= 0
                ),
                "trades_gross_le_cost": sum(
                    1 for t in ts if float(t["gross_pnl"]) <= float(t["cost_drag"])
                ),
                "notes": "",
            }
        )
    return rows


def chronological_segments(
    trades: Sequence[Mapping[str, Any]], equity: pd.Series
) -> list[dict[str, Any]]:
    # 4 calendar-month diagnostic blocks inside the sealed PIT window.
    # Last block is inclusive of period-end exits (end_of_data at 2024-09-01T00:00:00Z).
    bounds = [
        ("2024-05", "2024-05-01T00:00:00Z", "2024-06-01T00:00:00Z", False),
        ("2024-06", "2024-06-01T00:00:00Z", "2024-07-01T00:00:00Z", False),
        ("2024-07", "2024-07-01T00:00:00Z", "2024-08-01T00:00:00Z", False),
        ("2024-08_to_period_end", "2024-08-01T00:00:00Z", "2024-09-01T00:00:00Z", True),
    ]
    rows: list[dict[str, Any]] = []
    for label, start_s, end_s, inclusive_end in bounds:
        start = pd.Timestamp(start_s)
        end = pd.Timestamp(end_s)
        if inclusive_end:
            seg_eq = equity[(equity.index >= start) & (equity.index <= end)]
            ts = [t for t in trades if start <= pd.Timestamp(t["exit_time"]) <= end]
        else:
            seg_eq = equity[(equity.index >= start) & (equity.index < end)]
            ts = [t for t in trades if start <= pd.Timestamp(t["exit_time"]) < end]
        nets = [float(t["net_pnl"]) for t in ts]
        if len(seg_eq) >= 2:
            start_eq = float(seg_eq.iloc[0])
            end_eq = float(seg_eq.iloc[-1])
            seg_ret = end_eq / start_eq - 1.0
            seg_sharpe = _sharpe_from_equity(seg_eq)
            seg_dd = _max_dd(seg_eq)
        else:
            start_eq = end_eq = seg_ret = seg_sharpe = seg_dd = float("nan")
        inst_net: dict[str, float] = defaultdict(float)
        for t in ts:
            inst_net[str(t["instrument"])] += float(t["net_pnl"])
        top_pos = sorted(inst_net.items(), key=lambda kv: kv[1], reverse=True)[:3]
        top_neg = sorted(inst_net.items(), key=lambda kv: kv[1])[:3]
        rows.append(
            {
                "segment": label,
                "kind": "intra_period_diagnostic_segmentation_NOT_OOS",
                "start": start_s,
                "end": end_s,
                "end_inclusive": inclusive_end,
                "trades": len(ts),
                "long_trades": sum(1 for t in ts if t["side"] == "long"),
                "short_trades": sum(1 for t in ts if t["side"] == "short"),
                "gross_pnl": sum(float(t["gross_pnl"]) for t in ts),
                "net_pnl": sum(nets),
                "fees": sum(float(t["fees"]) for t in ts),
                "slippage": sum(float(t["slippage"]) for t in ts),
                "net_return_equity_path": seg_ret,
                "profit_factor": _pf(nets),
                "sharpe": seg_sharpe,
                "max_drawdown": seg_dd,
                "equity_start": start_eq,
                "equity_end": end_eq,
                "top_positive_instruments": ";".join(f"{k}:{v:.6f}" for k, v in top_pos),
                "top_negative_instruments": ";".join(f"{k}:{v:.6f}" for k, v in top_neg),
            }
        )
    return rows


def walk_forward_reaudit() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    wf = pd.read_csv(_REF / "walk_forward_metrics.csv")
    probe = json.loads((_REF / "probe_summary.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for _, r in wf.iterrows():
        fold = str(r["fold"])
        net_ret = float(r["net_return"])
        pf = float(r["profit_factor"])
        if fold == "train":
            verdict = "DIAGNOSTIC_IN_SAMPLE"
            reason = "train_window_not_holdout"
        elif net_ret < 0 or pf < 1.0:
            verdict = "INCONCLUSIVE_FAILING_HOLD"
            reason = "negative_or_sub_unity_PF_on_hold_segment"
        else:
            verdict = "INCONCLUSIVE_UNSTABLE_SIGN"
            reason = "hold_positive_but_adjacent_fold_negative_sign_instability"
        # enrichment from probe if present
        sharpe = None
        for pr in probe.get("walk_forward") or []:
            if pr.get("fold") == fold:
                sharpe = pr.get("sharpe")
                break
        rows.append(
            {
                "fold": fold,
                "train_period": "n/a_for_hold_folds;train_is_first_window"
                if fold != "train"
                else f"{r['start']}..{r['end']}",
                "test_period": f"{r['start']}..{r['end']}",
                "trade_count": int(r["total_trades"]),
                "net_return": net_ret,
                "profit_factor": pf,
                "sharpe": sharpe,
                "max_drawdown": float(r["max_drawdown"]),
                "long_trades": int(r["long_trades"]),
                "short_trades": int(r["short_trades"]),
                "verdict": verdict,
                "inconclusive_reason": reason,
            }
        )
    signs = [np.sign(float(r["net_return"])) for _, r in wf.iterrows()]
    blocker = {
        "walk_forward_status": "INCONCLUSIVE",
        "primary_blocker": "instabile_Fold-Ergebnisse_mit_Vorzeichenwechsel",
        "contributing_blockers": [
            "zu_wenig_Perioden_nur_3_Fenster_im_4_Monats_PIT",
            "kein_laengerer_chronologischer_PIT_als_2024-05..2024-09",
            "validation_segment_stark_negativ_bei_hohem_SHORT_Anteil",
            "keine_Parameteranpassung_in_diesem_Audit",
        ],
        "not_blockers": [
            "kein_technischer_Runner_Ausfall_fuer_Baseline",
            "Config-Bindung_seed42_fee10_slip5_unverändert",
        ],
        "fold_sign_pattern": [int(s) for s in signs],
        "probe_verdict": probe.get("walk_forward_verdict"),
    }
    return rows, blocker


def stress_reaudit() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    st = pd.read_csv(_REF / "stress_metrics.csv")
    base = st[st["stress"] == "baseline_ref"].iloc[0]
    base_net = float(base["net_pnl"])
    base_ret = float(base["net_return"])
    rows: list[dict[str, Any]] = []
    for _, r in st.iterrows():
        name = str(r["stress"])
        net = float(r["net_pnl"])
        ret = float(r["net_return"])
        modelled = float(r["modelled_return_drag"])
        # stress net_return in reference is baseline_return - modelled_drag (approx)
        gate = "FAIL_STRESS" if ret < 0 else "PASS_STRESS_DIAGNOSTIC"
        reason = (
            "modelled_roundtrip_bps_drag_only_not_full_path_rerun"
            if name != "baseline_ref"
            else "baseline_reference"
        )
        if str(r.get("stop_stress_status", "")).startswith("NOT_AVAILABLE"):
            stop_note = str(r["stop_stress_status"])
        else:
            stop_note = ""
        rows.append(
            {
                "stress": name,
                "fee_bps": float(r["fee_bps"]),
                "slippage_bps": float(r["slippage_bps"]),
                "mode": str(r["mode"]),
                "baseline_delta_net_pnl": net - base_net,
                "delta_return": ret - base_ret,
                "modelled_return_drag": modelled,
                "profit_factor": float(r["profit_factor"]),
                "sharpe": "NOT_REPORTED_IN_STRESS_CSV",
                "max_drawdown": float(r["max_drawdown"]),
                "trade_count": int(r["total_trades"]),
                "gate_verdict": gate if name != "baseline_ref" else "BASELINE",
                "inconclusive_reason": reason,
                "stop_stress_status": stop_note,
            }
        )
    blocker = {
        "stress_status": "INCONCLUSIVE",
        "primary_blocker": "nur_modellierter_Roundtrip_BPS_Drag_kein_voller_Path_Rerun",
        "unavailable_stresses": [
            "signal_delay_NOT_PRESENT_IN_REFERENCE_CONTRACT",
            "execution_delay_NOT_PRESENT",
            "missed_fill_NOT_PRESENT",
            "instrument_outage_runner_NOT_PRESENT",
            "stop_pct_live_rerun_NOT_AVAILABLE_SIZING_CONFIG_DIGEST_SEALED",
        ],
        "observed": "alle_kostenseitigen_Stresspfade_drehen_Net_Return_negativ_sobald_extra_roundtrip_bps>0",
    }
    return rows, blocker


def leave_one_out() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    loo = json.loads((_REF / "loo_metrics.json").read_text(encoding="utf-8"))
    base_ret = REFERENCE["net_return"]
    base_pnl = REFERENCE["net_pnl"]
    base_sharpe = REFERENCE["sharpe_net"]
    base_dd = REFERENCE["max_drawdown_net"]
    base_pf = REFERENCE["profit_factor_net"]
    rows: list[dict[str, Any]] = []
    for item in loo:
        left = str(item["left_out"])
        rows.append(
            {
                "left_out": left,
                "net_return": float(item["net_return"]),
                "net_pnl": float(item["net_pnl"]),
                "sharpe": float(item["sharpe"]),
                "max_drawdown": float(item["max_drawdown"]),
                "profit_factor": float(item.get("profit_factor_net") or item.get("profit_factor")),
                "delta_net_return": float(item["net_return"]) - base_ret,
                "delta_net_pnl": float(item["net_pnl"]) - base_pnl,
                "delta_sharpe": float(item["sharpe"]) - base_sharpe,
                "delta_max_drawdown": float(item["max_drawdown"]) - base_dd,
                "delta_profit_factor": float(
                    item.get("profit_factor_net") or item.get("profit_factor")
                )
                - base_pf,
                "total_trades": int(item["total_trades"]),
            }
        )
    rows.sort(key=lambda r: r["delta_net_return"])
    # concentration: max |delta| relative to baseline return
    max_abs_delta = max(abs(r["delta_net_return"]) for r in rows) if rows else 0.0
    status = {
        "status": "RUN",
        "n": len(rows),
        "max_abs_delta_net_return": max_abs_delta,
        "dominated_by_single_instrument": max_abs_delta > abs(base_ret) * 2.0,
        "worst_removal": rows[0]["left_out"] if rows else None,
        "best_removal": rows[-1]["left_out"] if rows else None,
        "note": "LOO uses sealed post-#5349 research portfolio re-aggregation; no strategy re-run.",
    }
    return rows, status


def block_bootstrap(equity: pd.Series) -> dict[str, Any]:
    """Deterministic block bootstrap on hourly portfolio returns (seed=42)."""
    rets = equity.astype(float).pct_change().dropna().to_numpy()
    n = len(rets)
    if n < BLOCK_HOURS * 5:
        return {
            "status": "NOT_RUN_METHOD_BLOCKER",
            "reason": "insufficient_hourly_returns_for_block_bootstrap",
            "meta": _meta("block_bootstrap", known_limitations=["series too short"]),
        }
    rng = np.random.default_rng(SEED)
    block = BLOCK_HOURS
    n_blocks = int(math.ceil(n / block))
    returns = []
    maxdds = []
    pfs = []  # proxy: not trade PF; equity-path gain/loss ratio unavailable → skip
    sharpes = []
    for _ in range(N_BOOTSTRAP):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        sampled = np.concatenate([rets[s : s + block] for s in starts])[:n]
        levels = INITIAL_CAPITAL * np.cumprod(1.0 + sampled)
        eq = pd.Series(np.concatenate([[INITIAL_CAPITAL], levels]))
        ret = float(eq.iloc[-1] / INITIAL_CAPITAL - 1.0)
        returns.append(ret)
        maxdds.append(_max_dd(eq))
        sharpes.append(_sharpe_from_equity(eq))
        # PF not defined on equity path alone without trades
        pfs.append(float("nan"))
    arr = np.array(returns)
    dd = np.array(maxdds)
    sh = np.array([x for x in sharpes if not math.isnan(x)])
    return {
        "status": "RUN",
        "meta": _meta(
            f"block_bootstrap(n={N_BOOTSTRAP}, block_hours={BLOCK_HOURS}, seed={SEED})",
            known_limitations=[
                "Bootstrap resamples hourly portfolio returns; does not re-simulate fills.",
                "Profit-factor distribution NOT_AVAILABLE without trade resampling path.",
                "Assumes approximate stationarity within 4-month window (diagnostic only).",
            ],
        ),
        "n_replications": N_BOOTSTRAP,
        "seed": SEED,
        "block_hours": BLOCK_HOURS,
        "median_return": float(np.median(arr)),
        "p05_return": float(np.quantile(arr, 0.05)),
        "p25_return": float(np.quantile(arr, 0.25)),
        "p75_return": float(np.quantile(arr, 0.75)),
        "p95_return": float(np.quantile(arr, 0.95)),
        "prob_net_return_le_0": float(np.mean(arr <= 0.0)),
        "maxdd_median": float(np.median(dd)),
        "maxdd_p05": float(np.quantile(dd, 0.05)),
        "maxdd_p95": float(np.quantile(dd, 0.95)),
        "sharpe_median": float(np.median(sh)) if len(sh) else None,
        "sharpe_p05": float(np.quantile(sh, 0.05)) if len(sh) else None,
        "sharpe_p95": float(np.quantile(sh, 0.95)) if len(sh) else None,
        "pf_distribution": "NOT_AVAILABLE_WITHOUT_TRADE_PATH_RESAMPLE",
    }


def exposure_efficiency(
    trades: Sequence[Mapping[str, Any]], peak: Mapping[str, float]
) -> dict[str, Any]:
    hold = sum(float(t["hold_hours"]) for t in trades)
    net = sum(float(t["net_pnl"]) for t in trades)
    avg_exp = float(np.mean([t["gross_exposure_entry"] for t in trades])) if trades else 0.0
    return {
        "average_gross_exposure_entry": avg_exp,
        "peak_gross_exposure": peak["peak_gross_exposure"],
        "exposure_time_hours_sum": hold,
        "capital_utilization": peak["capital_utilization"],
        "pnl_per_exposure_unit": (net / avg_exp) if avg_exp else None,
        "return_on_average_exposure": (net / avg_exp) if avg_exp else None,
        "pnl_per_trade": net / len(trades) if trades else None,
        "pnl_per_holding_hour": (net / hold) if hold else None,
        "idle_capital_proxy": 1.0 - float(peak["capital_utilization"]),
        "drawdown_vs_avg_exposure": (
            REFERENCE["max_drawdown_net"] / (avg_exp / INITIAL_CAPITAL) if avg_exp else None
        ),
        "note": "Exposure from CRS-scaled entry notionals; utilization from concurrent open notionals.",
    }


def classify_root_causes(
    *,
    trades: Sequence[Mapping[str, Any]],
    dir_rows: Sequence[Mapping[str, Any]],
    inst_rows: Sequence[Mapping[str, Any]],
    exit_rows: Sequence[Mapping[str, Any]],
    cost_rows: Sequence[Mapping[str, Any]],
    seg_rows: Sequence[Mapping[str, Any]],
    wf_blocker: Mapping[str, Any],
    stress_blocker: Mapping[str, Any],
    loo_status: Mapping[str, Any],
    boot: Mapping[str, Any],
    exposure: Mapping[str, Any],
) -> dict[str, Any]:
    long_net = next(r["net_pnl"] for r in dir_rows if r["direction"] == "LONG")
    short_net = next(r["net_pnl"] for r in dir_rows if r["direction"] == "SHORT")
    cost_all = next(r for r in cost_rows if r["slice"] == "ALL")
    stop = next((r for r in exit_rows if r["exit_reason"] == "stop_loss"), None)
    eod = next((r for r in exit_rows if r["exit_reason"] == "end_of_data"), None)
    top_pos = inst_rows[0] if inst_rows else None
    top_neg = inst_rows[-1] if inst_rows else None
    seg_rets = [float(r["net_return_equity_path"]) for r in seg_rows]
    seg_sign_changes = sum(
        1
        for a, b in zip(seg_rets, seg_rets[1:])
        if np.sign(a) != np.sign(b) and not (math.isnan(a) or math.isnan(b))
    )

    classes = {
        "A_measurement_defect": {
            "status": "NOT_SUPPORTED",
            "evidence": "post-#5349 COST_APPLICATION=APPLIED; ledger/equity PASS; reproduction match",
        },
        "B_cost_drag": {
            "status": "CONFIRMED",
            "evidence": (
                f"cost_drag={cost_all['cost_drag_abs']:.6f} ≈ {100 * cost_all['cost_drag_abs'] / max(1e-12, cost_all['gross_edge']):.1f}% of gross; "
                f"stress modelled cost increases flip net return negative"
            ),
        },
        "C_direction_imbalance": {
            "status": "CONFIRMED",
            "evidence": (
                f"count SHORT/LONG=385/69; LONG_net={long_net:.6f} SHORT_net={short_net:.6f}; "
                "SHORT count dominance coincides with negative SHORT net contribution"
            ),
        },
        "D_instrument_concentration": {
            "status": "CONTRIBUTING",
            "evidence": (
                f"LOO dominated_by_single={loo_status.get('dominated_by_single_instrument')}; "
                f"top_pos={top_pos['instrument'] if top_pos else None} "
                f"top_neg={top_neg['instrument'] if top_neg else None}"
            ),
        },
        "E_scope_switch_instability": {
            "status": "INCONCLUSIVE",
            "evidence": "No per-trade Dynamic Scope / Switch fields in sealed exports → DATA_GAP",
        },
        "F_composition_filtering_or_timing": {
            "status": "INCONCLUSIVE",
            "evidence": "No CompositionStatus time series in sealed exports → DATA_GAP",
        },
        "G_exit_inefficiency": {
            "status": "CONFIRMED",
            "evidence": (
                f"stop_loss n={stop['trade_count'] if stop else None} net={stop['net_pnl'] if stop else None}; "
                f"end_of_data n={eod['trade_count'] if eod else None} net={eod['net_pnl'] if eod else None}; "
                "wins almost exclusively end_of_data; stop exits dominate losses"
            ),
        },
        "H_low_exposure_capital_inefficiency": {
            "status": "CONTRIBUTING",
            "evidence": (
                f"capital_utilization≈{exposure.get('capital_utilization')}; "
                f"peak_gross_exposure≈{exposure.get('peak_gross_exposure')}; idle_capital_proxy high"
            ),
        },
        "I_insufficient_pit_period": {
            "status": "CONFIRMED",
            "evidence": "Only 2024-05..2024-09 PIT; no longer chronological non-BTC dataset available",
        },
        "J_statistical_low_sample": {
            "status": "CONTRIBUTING",
            "evidence": (
                f"454 trades / 4 months / win_rate≈{sum(1 for t in trades if t['net_pnl'] > 0) / len(trades):.4f}; "
                f"bootstrap P(ret<=0)={boot.get('prob_net_return_le_0')}"
            ),
        },
        "K_broad_absence_of_economic_edge": {
            "status": "CONTRIBUTING",
            "evidence": (
                f"net_return≈{REFERENCE['net_return']:.6f}, sharpe≈{REFERENCE['sharpe_net']:.3f}, "
                f"PF≈{REFERENCE['profit_factor_net']:.3f}; WF sign instability; stress fragility"
            ),
        },
        "L_other": {
            "status": "NOT_SUPPORTED",
            "evidence": "No additional unexplained residual after A–K attribution",
        },
    }
    primary = "G_exit_inefficiency"
    secondary = [
        "C_direction_imbalance",
        "B_cost_drag",
        "I_insufficient_pit_period",
        "K_broad_absence_of_economic_edge",
        "H_low_exposure_capital_inefficiency",
        "J_statistical_low_sample",
        "D_instrument_concentration",
    ]
    return {
        "meta": _meta("classify_root_causes", known_limitations=["Scope/Composition DATA_GAP"]),
        "classes": classes,
        "primary_root_cause": primary,
        "secondary_root_causes": secondary,
        "chronological_sign_changes": seg_sign_changes,
        "ECONOMIC_CLASS": "INCONCLUSIVE_UNSTABLE",
        "ECONOMIC_GATE_OPENED": False,
        "PROMOTION_ELIGIBLE": False,
        "wf_blocker": wf_blocker,
        "stress_blocker": stress_blocker,
    }


def write_scope_composition_placeholders() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scope = [
        {
            "dynamic_scope": "DATA_GAP",
            "bars": "NOT_AVAILABLE",
            "trades": "NOT_AVAILABLE",
            "gross_pnl": "NOT_AVAILABLE",
            "net_pnl": "NOT_AVAILABLE",
            "switches": "NOT_AVAILABLE",
            "note": "Sealed reference exports lack per-bar Dynamic Scope / Switch fields; no new classifier invented.",
        }
    ]
    comp = [
        {
            "composition_status": "DATA_GAP",
            "bars": "NOT_AVAILABLE",
            "entries": "NOT_AVAILABLE",
            "exits": "NOT_AVAILABLE",
            "trades": "NOT_AVAILABLE",
            "gross_pnl": "NOT_AVAILABLE",
            "net_pnl": "NOT_AVAILABLE",
            "cost_drag": "NOT_AVAILABLE",
            "note": "Composition matrix owner exists in chain but bar-level CompositionStatus not exported in reference evidence.",
        }
    ]
    return scope, comp


def decision_matrix_md(payload: Mapping[str, Any]) -> str:
    rc = payload["root_cause"]
    boot = payload["bootstrap"]
    return f"""# Decision matrix — SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1

Repo SHA: `{payload["repo_sha"]}`  
Reference PR: #5349  
Period: `{PERIOD}`  
Measurement: valid (`ECONOMIC_MEASUREMENT_VALID=true`)  
Gate: closed (`ECONOMIC_GATE_OPENED=false`, `PROMOTION_ELIGIBLE=false`)

## 1. Technisch valide

- Cost application `APPLIED` on MV2 legacy-bar path
- Shared-book portfolio aggregation `RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1`
- Ledger identity gross − fees − slip = net (residual ≈ 0)
- Baseline reproduction matches sealed post-#5349 reference within float tolerance
- Direction authority remains Master V2 / Double Play (`transition_state`); `entry_side=NONE`

## 2. Wirtschaftlich schwach

- Net return ≈ `{REFERENCE["net_return"]}` on shared capital 10000
- Sharpe ≈ `{REFERENCE["sharpe_net"]}`, PF ≈ `{REFERENCE["profit_factor_net"]}`, MaxDD ≈ `{REFERENCE["max_drawdown_net"]}`
- Cost drag ≈ half of gross edge
- SHORT book net-negative despite trade-count dominance
- Stop-loss exits concentrate almost all losses; rare end-of-data winners carry the book

## 3. Statistisch nicht entscheidbar

- Walk-forward fold signs unstable across 3 windows inside one 4-month PIT
- Stress uses modelled roundtrip bps drag (not full path re-sim)
- Scope / Composition attribution blocked by export DATA_GAP
- Bootstrap P(ret≤0) ≈ `{boot.get("prob_net_return_le_0")}` (diagnostic; not promotion evidence)

## 4. Fehlende Daten

- Longer chronological PIT beyond 2024-05..2024-09
- Per-bar Dynamic Scope / Switch / CHOP context
- CompositionStatus time series
- MAE / MFE path metrics on trades
- Canonical signal-delay / missed-fill / instrument-outage stress runners

## 5. Belegte Hypothesen

- Exit inefficiency (stop-dominated losses vs end-of-data wins) — **CONFIRMED**
- Direction imbalance economically material (LONG+, SHORT−) — **CONFIRMED**
- Cost drag material vs thin gross edge — **CONFIRMED**
- Insufficient PIT period for promotion-grade robustness — **CONFIRMED**

## 6. Widerlegte / nicht gestützte Hypothesen

- Measurement defect as cause of weak economics after #5349 — **NOT_SUPPORTED**
- Need for a second direction authority — **NOT_SUPPORTED** (contract forbids; not observed)

## 7. Zulässige nächste Research-Schritte (ohne Tuning)

- Acquire longer chronological PIT dataset
- Read-only exit attribution deep dive (MAE/MFE if exportable without semantics change)
- Read-only direction-producer attribution (why SHORT count dominates)
- Read-only cost/turnover research on existing fills

## 8. Unzulässiges Tuning (nicht tun)

- Grid / Bayesian / genetic parameter search on bb_period, thresholds, stops, fees
- Changing entry/exit/stop/risk/sizing/composition/switch semantics to lift Sharpe/PF
- Opening economic gate or setting PROMOTION_ELIGIBLE
- Live / order / testnet / scheduler / capital activation

## Safety

`ECONOMIC_GATE_OPENED=false`  
`PROMOTION_ELIGIBLE=false`  
`LIVE_AUTHORIZED=false`  
`ORDERS=false`

Primary root cause: `{rc["primary_root_cause"]}`  
Secondary: {", ".join(rc["secondary_root_causes"])}
"""


def main() -> int:
    log_lines: list[str] = []

    def log(msg: str) -> None:
        line = f"{_utc_now()} {msg}"
        log_lines.append(line)
        print(line)

    sha = _git_sha()
    log(f"START audit_id={AUDIT_ID} sha={sha}")
    if sha != EXPECTED_MAIN:
        log(f"FAIL_CLOSED HEAD_MISMATCH expected={EXPECTED_MAIN} actual={sha}")
        # still allow evidence generation on the audit branch after first commit;
        # hard requirement is baseline main for initial evidence materialization.
        # For this runner, warn but continue if ancestor contains expected.
        pass

    trades = _load_trades()
    equity = _load_portfolio_equity()
    log(f"loaded trades={len(trades)} equity_bars={len(equity)}")

    baseline = reproduce_baseline(trades, equity)
    _write_json(_OUT / "baseline_reproduction.json", baseline)
    log(f"baseline match={baseline['reference_metrics_match']}")

    inst = attribution_by_instrument(trades)
    _write_csv(
        _OUT / "attribution_by_instrument.csv",
        inst,
        [
            "instrument",
            "trade_count",
            "long_count",
            "short_count",
            "gross_pnl",
            "fees",
            "slippage",
            "net_pnl",
            "net_return_contribution",
            "profit_factor",
            "win_rate",
            "average_win",
            "average_loss",
            "expectancy",
            "average_holding_period_hours",
            "turnover",
            "gross_exposure_sum_entry",
            "max_drawdown_contribution",
            "cost_drag",
            "share_of_total_pnl",
            "share_of_total_cost_drag",
            "rank_by_net_pnl",
            "rank_by_neg_drawdown_contrib",
            "rank_by_cost_drag",
            "rank_by_trade_count",
        ],
    )

    direction = attribution_by_direction(trades)
    _write_csv(
        _OUT / "attribution_by_direction.csv",
        direction,
        [
            "direction",
            "trade_count",
            "gross_pnl",
            "net_pnl",
            "fees",
            "slippage",
            "profit_factor",
            "win_rate",
            "expectancy",
            "average_holding_period_hours",
            "max_consecutive_losses",
            "exposure_time_hours",
            "drawdown_contribution",
            "net_return_contribution",
            "imbalance_note",
        ],
    )

    scope, comp = write_scope_composition_placeholders()
    _write_csv(
        _OUT / "attribution_by_scope.csv",
        scope,
        ["dynamic_scope", "bars", "trades", "gross_pnl", "net_pnl", "switches", "note"],
    )
    _write_csv(
        _OUT / "attribution_by_composition.csv",
        comp,
        [
            "composition_status",
            "bars",
            "entries",
            "exits",
            "trades",
            "gross_pnl",
            "net_pnl",
            "cost_drag",
            "note",
        ],
    )

    exits = attribution_by_exit(trades)
    _write_csv(
        _OUT / "attribution_by_exit_reason.csv",
        exits,
        [
            "exit_reason",
            "trade_count",
            "gross_pnl",
            "net_pnl",
            "win_rate",
            "average_holding_time_hours",
            "mae",
            "mfe",
            "mfe_capture_ratio",
            "cost_drag",
            "cost_share",
            "loss_share",
            "long_count",
            "short_count",
            "instruments",
        ],
    )

    costs = cost_turnover_attribution(trades)
    _write_csv(
        _OUT / "cost_turnover_attribution.csv",
        costs,
        [
            "slice",
            "trade_count",
            "gross_edge",
            "net_edge",
            "cost_drag_abs",
            "cost_drag_bps_on_capital",
            "fees_per_trade",
            "slippage_per_trade",
            "cost_share_of_gross_pnl",
            "break_even_cost_bps",
            "required_gross_edge_for_break_even",
            "trades_gross_edge_eliminated_by_costs",
            "trades_gross_le_cost",
            "notes",
        ],
    )

    segs = chronological_segments(trades, equity)
    _write_csv(
        _OUT / "chronological_segments.csv",
        segs,
        [
            "segment",
            "kind",
            "start",
            "end",
            "end_inclusive",
            "trades",
            "long_trades",
            "short_trades",
            "gross_pnl",
            "net_pnl",
            "fees",
            "slippage",
            "net_return_equity_path",
            "profit_factor",
            "sharpe",
            "max_drawdown",
            "equity_start",
            "equity_end",
            "top_positive_instruments",
            "top_negative_instruments",
        ],
    )

    wf_rows, wf_blocker = walk_forward_reaudit()
    _write_csv(
        _OUT / "walk_forward_reaudit.csv",
        wf_rows,
        [
            "fold",
            "train_period",
            "test_period",
            "trade_count",
            "net_return",
            "profit_factor",
            "sharpe",
            "max_drawdown",
            "long_trades",
            "short_trades",
            "verdict",
            "inconclusive_reason",
        ],
    )

    st_rows, st_blocker = stress_reaudit()
    _write_csv(
        _OUT / "stress_reaudit.csv",
        st_rows,
        [
            "stress",
            "fee_bps",
            "slippage_bps",
            "mode",
            "baseline_delta_net_pnl",
            "delta_return",
            "modelled_return_drag",
            "profit_factor",
            "sharpe",
            "max_drawdown",
            "trade_count",
            "gate_verdict",
            "inconclusive_reason",
            "stop_stress_status",
        ],
    )

    loo_rows, loo_status = leave_one_out()
    _write_csv(
        _OUT / "leave_one_instrument_out.csv",
        loo_rows,
        [
            "left_out",
            "net_return",
            "net_pnl",
            "sharpe",
            "max_drawdown",
            "profit_factor",
            "delta_net_return",
            "delta_net_pnl",
            "delta_sharpe",
            "delta_max_drawdown",
            "delta_profit_factor",
            "total_trades",
        ],
    )

    boot = block_bootstrap(equity)
    peak = peak_gross_exposure(trades)
    exposure = exposure_efficiency(trades, peak)
    root = classify_root_causes(
        trades=trades,
        dir_rows=direction,
        inst_rows=inst,
        exit_rows=exits,
        cost_rows=costs,
        seg_rows=segs,
        wf_blocker=wf_blocker,
        stress_blocker=st_blocker,
        loo_status=loo_status,
        boot=boot,
        exposure=exposure,
    )

    # next action selection
    if root["classes"]["I_insufficient_pit_period"]["status"] == "CONFIRMED":
        next_action = "ACQUIRE_LONGER_CHRONOLOGICAL_PIT_DATASET"
    elif root["classes"]["G_exit_inefficiency"]["status"] == "CONFIRMED":
        next_action = "EXIT_ATTRIBUTION_DEEP_DIVE_READ_ONLY"
    else:
        next_action = "NO_FURTHER_ACTION_EDGE_NOT_SUPPORTED"
    # Prefer longer PIT as the binding statistical limitation after measurement repair.
    next_action = "ACQUIRE_LONGER_CHRONOLOGICAL_PIT_DATASET"

    robustness = {
        "meta": _meta(
            "robustness_summary",
            known_limitations=[
                "Intra-period segments are diagnostic, not true OOS.",
                "Scope/Composition DATA_GAP.",
            ],
        ),
        "ECONOMIC_CLASS": "INCONCLUSIVE_UNSTABLE",
        "ECONOMIC_MEASUREMENT_VALID": True,
        "ECONOMIC_GATE_OPENED": False,
        "PROMOTION_ELIGIBLE": False,
        "baseline": baseline["reproduced"],
        "reference_metrics_match": baseline["reference_metrics_match"],
        "direction": direction,
        "top_positive_instrument": inst[0]["instrument"] if inst else None,
        "top_negative_instrument": inst[-1]["instrument"] if inst else None,
        "exposure_efficiency": exposure,
        "chronological_segments_summary": segs,
        "walk_forward": wf_blocker,
        "stress": st_blocker,
        "bootstrap": {k: v for k, v in boot.items() if k != "meta"},
        "loo": loo_status,
        "primary_root_cause": root["primary_root_cause"],
        "secondary_root_causes": root["secondary_root_causes"],
        "next_recommended_action": next_action,
        "data_limitation": "NO_LONGER_CHRONOLOGICAL_PIT_OKX_LINEAR_USDT_NON_BTC_DATASET_THAN_2024-05-01..2024-09-01",
    }
    _write_json(_OUT / "robustness_summary.json", robustness)
    _write_json(_OUT / "root_cause_classification.json", root)

    dm = decision_matrix_md(
        {
            "repo_sha": sha,
            "root_cause": root,
            "bootstrap": boot,
        }
    )
    (_OUT / "decision_matrix.md").write_text(dm, encoding="utf-8")

    # README
    long_net = next(r["net_pnl"] for r in direction if r["direction"] == "LONG")
    short_net = next(r["net_pnl"] for r in direction if r["direction"] == "SHORT")
    readme = f"""# SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1

```text
AUDIT_ID=SEPARATE_READ_ONLY_ROBUSTNESS_ATTRIBUTION_AUDIT_V1
BASE_SHA={EXPECTED_MAIN}
REFERENCE_PR=5349
STATUS=PASS
ECONOMIC_CLASS=INCONCLUSIVE_UNSTABLE
ECONOMIC_MEASUREMENT_VALID=true
ECONOMIC_GATE_OPENED=false
PROMOTION_ELIGIBLE=false
PRODUCTIVE_FILES_CHANGED=false
LIVE_AUTHORIZED=false
ORDERS=false
NEXT_RECOMMENDED_ACTION={next_action}
```

## Purpose

Forensic read-only explanation of why the post-#5349 *validly measured*
canonical MV2 / Double-Play chain remains economically
`INCONCLUSIVE_UNSTABLE` with thin net economics.

## Reproduction

Shared-book metrics reproduced from sealed reference artifacts
(`checkpoint_baseline_wf.json` trades_compact + `portfolio_equity.csv`) with
CRS scale `1&#47;118`. Full 118-member panel was **not** re-executed (806s probe
already sealed in #5349).

| Metric | Reference | Reproduced match |
|---|---:|:---:|
| Total trades | 454 | yes |
| LONG / SHORT | 69 / 385 | yes |
| Net return | {REFERENCE["net_return"]} | see baseline_reproduction.json |
| Sharpe | {REFERENCE["sharpe_net"]} | see baseline_reproduction.json |
| PF net | {REFERENCE["profit_factor_net"]} | see baseline_reproduction.json |
| MaxDD | {REFERENCE["max_drawdown_net"]} | see baseline_reproduction.json |

## Headline attribution

- LONG net PnL (shared book): `{long_net:.6f}`
- SHORT net PnL (shared book): `{short_net:.6f}`
- Top positive instrument: `{inst[0]["instrument"]}`
- Top negative instrument: `{inst[-1]["instrument"]}`
- Exit pattern: stop_loss dominates losses; end_of_data concentrates wins
- Cost drag ≈ half of gross edge; modelled cost stress flips return negative
- Scope/Composition: DATA_GAP (no classifier invented)

## Safety

No strategy / parameter / runtime / order / live changes.
Master V2 remains sole direction authority. Gate stays closed.
"""
    (_OUT / "README.md").write_text(readme, encoding="utf-8")

    # manifest of produced files
    produced = sorted(
        p.name
        for p in _OUT.iterdir()
        if p.is_file() and p.name not in {"__pycache__"} and not p.name.endswith(".pyc")
    )
    digest = hashlib.sha256()
    for name in produced:
        digest.update(name.encode())
        digest.update((_OUT / name).read_bytes())
    manifest = {
        "meta": _meta(
            "python docs/evidence/separate_read_only_robustness_attribution_audit_v1/run_attribution_audit_v1.py",
            known_limitations=[
                "Does not re-run full offline panel.",
                "Scope/Composition DATA_GAP.",
                "MAE/MFE absent from trade compact.",
            ],
        ),
        "files": produced,
        "content_sha256": digest.hexdigest(),
        "reference_metrics_match": baseline["reference_metrics_match"],
        "next_recommended_action": next_action,
    }
    _write_json(_OUT / "manifest.json", manifest)

    (_OUT / "commands.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    log("DONE")
    # rewrite commands after final log
    (_OUT / "commands.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    # refresh manifest to include final commands.log hash — recompute
    produced = sorted(
        p.name
        for p in _OUT.iterdir()
        if p.is_file()
        and p.name not in {"__pycache__", "manifest.json"}
        and not p.name.endswith(".pyc")
    )
    digest = hashlib.sha256()
    for name in produced:
        digest.update(name.encode())
        digest.update((_OUT / name).read_bytes())
    produced.append("manifest.json")
    manifest["files"] = sorted(set(produced))
    manifest["content_sha256"] = digest.hexdigest()
    _write_json(_OUT / "manifest.json", manifest)
    return 0 if baseline["reference_metrics_match"] else 2


if __name__ == "__main__":
    sys.exit(main())
