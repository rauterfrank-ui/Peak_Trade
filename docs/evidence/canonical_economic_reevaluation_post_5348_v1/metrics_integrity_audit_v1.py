#!/usr/bin/env python3
"""NON-AUTHORITATIVE metrics-integrity audit for post-#5348 economic evidence.

Reads checkpoint_baseline_wf.json + live one-instrument cost spot-check conclusions.
Does not mutate productive trading code. Regenerates integrity evidence and corrected
reporting fields under this evidence directory.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Optional

EVIDENCE = Path(__file__).resolve().parent
CHECKPOINT = EVIDENCE / "checkpoint_baseline_wf.json"
INITIAL_CAPITAL_PER_INSTRUMENT = 10_000.0
FEE_BPS_CONFIG = 10.0
SLIPPAGE_BPS_CONFIG = 5.0
NA = "NOT_AVAILABLE"


def _num(v: Any) -> Optional[float]:
    if isinstance(v, (int, float)) and not (
        isinstance(v, float) and (math.isnan(v) or math.isinf(v))
    ):
        return float(v)
    return None


def _pf(wins: float, losses_abs: float) -> Any:
    if losses_abs <= 0.0:
        return NA if wins <= 0.0 else float("inf")
    return wins / losses_abs


def _load_checkpoint() -> dict[str, Any]:
    return json.loads(CHECKPOINT.read_text(encoding="utf-8"))


def analyze(checkpoint: dict[str, Any]) -> dict[str, Any]:
    rows = list(checkpoint["baseline_rows"])
    prior_agg = dict(checkpoint.get("baseline_agg") or {})

    trades: list[dict[str, Any]] = []
    for r in rows:
        for t in r.get("trades_compact") or []:
            row = dict(t)
            row["instrument"] = r.get("instrument")
            row["member_id"] = r.get("member_id")
            row["instrument_initial_equity"] = _num(r.get("initial_equity")) or (
                INITIAL_CAPITAL_PER_INSTRUMENT
            )
            trades.append(row)

    gross_vals = [_num(t.get("gross_pnl")) for t in trades]
    net_vals = [_num(t.get("pnl")) for t in trades]
    fee_vals = [_num(t.get("fee")) for t in trades]
    entry_costs = [_num(t.get("entry_cost")) for t in trades]
    exit_costs = [_num(t.get("exit_cost")) for t in trades]

    gross_f = [x for x in gross_vals if x is not None]
    net_f = [x for x in net_vals if x is not None]
    fee_f = [x for x in fee_vals if x is not None]
    entry_f = [x for x in entry_costs if x is not None]
    exit_f = [x for x in exit_costs if x is not None]

    gross_pnl = float(sum(gross_f)) if gross_f else 0.0
    net_pnl = float(sum(net_f)) if net_f else 0.0
    fees_from_fee_field = float(sum(fee_f)) if fee_f else 0.0
    fees_from_entry_exit = float(sum(entry_f) + sum(exit_f)) if (entry_f or exit_f) else 0.0
    # Prefer explicit entry/exit cost components when present; else fee field.
    fees_total = fees_from_entry_exit if (entry_f or exit_f) else fees_from_fee_field
    cost_drag_ledger = float(gross_pnl - net_pnl)
    # Separable slippage is not present in compact ledger; treat as 0 unless fields exist.
    slippage_total = 0.0

    long_n = sum(1 for t in trades if t.get("side") == "long")
    short_n = sum(1 for t in trades if t.get("side") == "short")
    exit_reasons = Counter(str(t.get("exit_reason") or "unspecified") for t in trades)
    stop_like = sum(
        1 for t in trades if t.get("stop_hit") or "stop" in str(t.get("exit_reason") or "").lower()
    )

    instrument_returns = [
        _num(r.get("net_return")) for r in rows if _num(r.get("net_return")) is not None
    ]
    prior_sum_returns = float(sum(instrument_returns)) if instrument_returns else 0.0
    n_instruments = len(rows)
    traded_instruments = sum(1 for r in rows if int(r.get("total_trades") or 0) > 0)
    panel_denom = n_instruments * INITIAL_CAPITAL_PER_INSTRUMENT
    equal_capital_panel_return = (net_pnl / panel_denom) if panel_denom else NA

    # Prior harness mistakenly treated modelled slip as trade_count * 2 * slip_bps.
    prior_fake_slippage_drag = float(len(trades) * 2.0 * SLIPPAGE_BPS_CONFIG)

    # Trade-level PF from gross legs (same as prior PF source, but documented).
    wins = sum(x for x in gross_f if x > 0)
    losses = abs(sum(x for x in gross_f if x < 0))
    profit_factor = _pf(wins, losses)

    # Cost application: configured but ledger shows zero separable costs and gross==net.
    costs_configured = True
    costs_in_ledger = abs(fees_total) > 1e-12 or abs(cost_drag_ledger) > 1e-12
    cost_application = "PASS" if costs_in_ledger else "NOT_APPLIED"

    # Live spot-check (1INCH) documented in cost_reconciliation.json:
    # entry_price == bar_close (0 bps), entry_cost=exit_cost=0, fee_drag=0,
    # economic_interpretation_allowed=false, LEGACY_PATH_COST_APPLICATION=false.
    capital_double_counting = abs(prior_sum_returns - equal_capital_panel_return) > 1e-6

    ledger_recon_ok = abs((gross_pnl - fees_total - slippage_total) - net_pnl) < 1e-6
    # No single portfolio equity exists across instruments.
    equity_recon = "FAIL"

    economic_measurement_valid = bool(
        costs_in_ledger and (not capital_double_counting) and ledger_recon_ok
    )
    # With NOT_APPLIED costs + double-counted return, measurement is invalid.
    if cost_application == "NOT_APPLIED" or capital_double_counting:
        economic_measurement_valid = False

    economic_class = (
        "INVALID_ECONOMIC_MEASUREMENT"
        if not economic_measurement_valid
        else prior_agg.get("economic_class", "PARTIAL")
    )

    return {
        "total_trades": len(trades),
        "long_trades": long_n,
        "short_trades": short_n,
        "instruments": n_instruments,
        "traded_instruments": traded_instruments,
        "gross_pnl": gross_pnl,
        "net_pnl": net_pnl,
        "fees_total": fees_total,
        "slippage_total": slippage_total,
        "cost_drag": cost_drag_ledger,
        "fee_bps_config": FEE_BPS_CONFIG,
        "slippage_bps_config": SLIPPAGE_BPS_CONFIG,
        "costs_configured": costs_configured,
        "cost_application": cost_application,
        "prior_net_return_sum_instrument_returns": prior_sum_returns,
        "prior_net_return_invalid": True,
        "net_return_equal_capital_panel": equal_capital_panel_return,
        "net_return_definition": (
            "equal_capital_panel_return = sum_i(net_pnl_i) / (N_instruments * initial_capital); "
            "prior exported value was INVALID sum of independent instrument total_returns"
        ),
        "initial_capital_per_instrument": INITIAL_CAPITAL_PER_INSTRUMENT,
        "portfolio_aggregation": (
            "independent_per_instrument_equity_curves; no shared portfolio equity"
        ),
        "capital_double_counting": capital_double_counting,
        "profit_factor_trade_gross": profit_factor,
        "sharpe_prior_cross_sectional": prior_agg.get("sharpe"),
        "sharpe_prior_invalid": True,
        "sharpe_corrected": NA,
        "sharpe_definition": (
            "prior=mean(instrument_net_return)/std(instrument_net_return) "
            "(cross-section, not time-series); corrected=NOT_AVAILABLE without "
            "single portfolio equity curve"
        ),
        "max_drawdown_prior_worst_instrument": prior_agg.get("max_drawdown"),
        "max_drawdown_definition": ("prior=min(instrument max_drawdown); not a portfolio drawdown"),
        "exit_reasons": dict(sorted(exit_reasons.items())),
        "stop_like_exits": stop_like,
        "prior_fake_slippage_drag_bps_trades_unit": prior_fake_slippage_drag,
        "ledger_reconciliation": "PASS" if ledger_recon_ok else "FAIL",
        "equity_reconciliation": equity_recon,
        "economic_measurement_valid": economic_measurement_valid,
        "economic_class": economic_class,
        "ECONOMIC_GATE_OPENED": False,
        "PROMOTION_ELIGIBLE": False,
        "first_loss_boundaries": [
            "COST_NOT_APPLIED_IN_ROUNDTRIP_LEDGER: entry_cost=exit_cost=fee_drag=0 "
            "despite fee_bps=10 slippage_bps=5; LEGACY_PATH_COST_APPLICATION=false; "
            "economic_interpretation_allowed=false; entry fill at bar close (0 bps)",
            "NET_RETURN_SUM_OF_INSTRUMENT_RETURNS: prior panel net_return summed "
            "118 independent total_returns (capital double-counting)",
            "SHARPE_CROSS_SECTIONAL_PROXY: prior panel sharpe was mean/std of "
            "instrument returns, not annualized equity-curve Sharpe",
            "NO_SINGLE_PORTFOLIO_EQUITY: max_drawdown/return/sharpe cannot share "
            "one equity ledger across instruments",
        ],
    }


def write_reconciliation_csv(trades: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "instrument",
        "member_id",
        "side",
        "entry_time",
        "exit_time",
        "exit_reason",
        "gross_pnl",
        "fee",
        "entry_cost",
        "exit_cost",
        "slippage",
        "net_pnl",
        "recon_residual",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for t in trades:
            g = _num(t.get("gross_pnl")) or 0.0
            fee = _num(t.get("fee")) or 0.0
            entry_c = _num(t.get("entry_cost")) or 0.0
            exit_c = _num(t.get("exit_cost")) or 0.0
            # Prefer component costs when present.
            costs = (entry_c + exit_c) if (entry_c or exit_c) else fee
            slip = 0.0
            n = _num(t.get("pnl")) or 0.0
            w.writerow(
                {
                    "instrument": t.get("instrument"),
                    "member_id": t.get("member_id"),
                    "side": t.get("side"),
                    "entry_time": t.get("entry_time"),
                    "exit_time": t.get("exit_time"),
                    "exit_reason": t.get("exit_reason"),
                    "gross_pnl": g,
                    "fee": fee,
                    "entry_cost": entry_c,
                    "exit_cost": exit_c,
                    "slippage": slip,
                    "net_pnl": n,
                    "recon_residual": g - costs - slip - n,
                }
            )


def main() -> int:
    ck = _load_checkpoint()
    result = analyze(ck)

    rows = list(ck["baseline_rows"])
    trades: list[dict[str, Any]] = []
    for r in rows:
        for t in r.get("trades_compact") or []:
            row = dict(t)
            row["instrument"] = r.get("instrument")
            row["member_id"] = r.get("member_id")
            trades.append(row)

    write_reconciliation_csv(trades, EVIDENCE / "economic_ledger_reconciliation.csv")

    cost_recon = {
        "fee_bps_config": FEE_BPS_CONFIG,
        "slippage_bps_config": SLIPPAGE_BPS_CONFIG,
        "stop_pct_config": 0.025,
        "costs_configured_in_runtime_evaluation_config": True,
        "cost_application": result["cost_application"],
        "fees_total_ledger": result["fees_total"],
        "slippage_total_ledger": result["slippage_total"],
        "cost_drag_ledger_gross_minus_net": result["cost_drag"],
        "prior_exported_cost_drag": 0.0,
        "prior_exported_slippage_drag_invalid_unit": result[
            "prior_fake_slippage_drag_bps_trades_unit"
        ],
        "prior_slippage_drag_unit": "bps_times_trades_NOT_currency",
        "live_spot_check_1INCH": {
            "entry_fill_vs_bar_close_bps": 0.0,
            "entry_cost": 0.0,
            "exit_cost": 0.0,
            "fee_drag_stats": 0.0,
            "slippage_impact_stats": 0.0,
            "economic_interpretation_allowed": False,
            "legacy_path_cost_application": False,
            "conclusion": "CONFIGURED_BUT_NOT_APPLIED_TO_LEDGER_OR_FILLS",
        },
        "engine_notes": [
            "src/backtest/engine.py LEGACY_PATH_COST_APPLICATION=False zeros "
            "entry_cost/exit_cost on legacy Trade accounting path",
            "stop_loss roundtrips observed with entry_cost=exit_cost=0 and pnl==gross_pnl",
            "EffectiveBacktestCostConfigV0.economic_interpretation_allowed=False",
        ],
        "reconciliation_identity": "gross_pnl - fees - slippage = net_pnl",
        "reconciliation_status": result["ledger_reconciliation"],
    }
    (EVIDENCE / "cost_reconciliation.json").write_text(
        json.dumps(cost_recon, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    metrics_def = """# Metrics definitions — post-#5348 integrity audit

## Scope

Audit of exported panel metrics from
`docs/evidence/canonical_economic_reevaluation_post_5348_v1` against the
canonical offline roundtrip ledger produced by
`run_mv2_research_backtest_wiring_v1` (seed 42).

## Per-metric contract

| Metric | Formula | Unit | Aggregation | Denominator | Annualization | Parallel instruments | Open positions | Ledger source |
|--------|---------|------|-------------|-------------|---------------|----------------------|----------------|---------------|
| gross_pnl | Σ trade.gross_pnl | currency | panel sum of trades | n/a | none | sum across independent instrument runs | closed roundtrips only in trades table | trade.gross_pnl |
| fees | Σ (entry_cost+exit_cost) else Σ fee | currency | panel sum | n/a | none | sum | closed only | entry_cost/exit_cost/fee |
| slippage | separable slippage fields (none observed) | currency | panel sum | n/a | none | sum | closed only | **not present** / 0 |
| net_pnl | Σ trade.pnl | currency | panel sum | n/a | none | sum | closed only | trade.pnl |
| cost_drag | gross_pnl − net_pnl | currency | panel | n/a | none | derived | closed only | identity |
| equity | per-instrument equity_curve | currency | **no portfolio curve** | initial 10000/instrument | n/a | independent | MTM while open | BacktestResult.equity_curve |
| net_return (prior export) | Σ instrument total_return | return | **INVALID sum** | each instrument 10000 | none | **double-counts capital** | uses closed stats total_return | stats/metrics total_return |
| net_return (corrected) | Σ net_pnl / (N × 10000) | return | equal-capital panel proxy | N×10000 | none | equal capital assumed | closed pnl only | derived |
| profit_factor | Σ gross_wins / \\|Σ gross_losses\\| | ratio | trade gross legs | n/a | none | pooled trades | closed only | trade.gross_pnl |
| sharpe (prior export) | mean(r_i)/std(r_i) over instruments | ratio | cross-section | instrument returns | **none / not TS** | cross-section | n/a | instrument net_return |
| sharpe (corrected) | NOT_AVAILABLE | n/a | requires portfolio equity TS | n/a | n/a | n/a | n/a | none |
| max_drawdown (prior) | min_i DD_i | return | worst instrument | per-instrument equity | none | not portfolio DD | per curve | metrics max_drawdown |

## Configured costs

- `fee_bps=10.0`, `slippage_bps=5.0`, `stop_pct=0.025`
- Bound break-even roundtrip = 30 bps when costs are applied
- Observed ledger: fees=0, slippage=0, cost_drag=0, fill at bar close

## Validity

`ECONOMIC_MEASUREMENT_VALID=false` because costs are **NOT_APPLIED** in the
roundtrip ledger and the prior panel return/Sharpe aggregation is invalid.
"""
    (EVIDENCE / "metrics_definitions.md").write_text(metrics_def, encoding="utf-8")

    portfolio_md = f"""# Portfolio aggregation audit — post-#5348

## Method used in prior export

Each of the {result["instruments"]} instruments was backtested independently with
`initial_cash = {INITIAL_CAPITAL_PER_INSTRUMENT}`.

Prior panel `NET_RETURN={result["prior_net_return_sum_instrument_returns"]}` was
computed as the **sum of per-instrument `total_return` values**.

## Capital double-counting

`CAPITAL_DOUBLE_COUNTING=true`.

Summing independent returns implicitly treats each instrument's full initial
capital as additive portfolio capital without a shared equity curve:

- prior sum-of-returns: `{result["prior_net_return_sum_instrument_returns"]}`
- equal-capital panel proxy `sum(net_pnl)/(N*10000)`: `{result["net_return_equal_capital_panel"]}`

These differ by ~{abs(float(result["prior_net_return_sum_instrument_returns"]) - float(result["net_return_equal_capital_panel"])):.6f}.

## Equity reconciliation

`EQUITY_RECONCILIATION=FAIL` — there is **no** single portfolio equity series.
Therefore panel Sharpe / portfolio max-drawdown / portfolio net-return cannot be
sourced from one canonical equity ledger.

## Corrected aggregation (reporting only)

| Field | Value |
|------|------:|
| gross_pnl (sum trades) | {result["gross_pnl"]} |
| net_pnl (sum trades) | {result["net_pnl"]} |
| equal-capital panel return | {result["net_return_equal_capital_panel"]} |
| profit_factor (trade gross) | {result["profit_factor_trade_gross"]} |
| sharpe corrected | {result["sharpe_corrected"]} |
| portfolio equity | NOT_AVAILABLE |

## First-loss boundary

`NET_RETURN_SUM_OF_INSTRUMENT_RETURNS` in audit harness `_aggregate_rows`.
"""
    (EVIDENCE / "portfolio_aggregation_audit.md").write_text(portfolio_md, encoding="utf-8")

    verdict = f"""# Metrics integrity verdict — post-#5348

## STATUS=`FAIL`

## ECONOMIC_MEASUREMENT_VALID=`false`

## ECONOMIC_CLASS=`INVALID_ECONOMIC_MEASUREMENT`

The previously exported economic panel metrics are **not** a valid portfolio
measurement:

1. **Costs NOT_APPLIED** — fee_bps/slippage_bps are configured, but roundtrip
   ledger shows `entry_cost=exit_cost=0`, `fee_drag=0`, `pnl==gross_pnl`, and
   entry fills at bar close (0 bps). `COST_DRAG=0.0` is ledger-true but
   economically misleading.
2. **Capital double-counting** — prior `NET_RETURN` summed independent
   instrument returns.
3. **Sharpe mismatch** — prior panel Sharpe was a cross-sectional mean/std of
   instrument returns, not an equity-curve Sharpe; hence a tiny Sharpe can
   coexist with a large (invalid) summed return.
4. **No shared equity ledger** — PF/DD/Sharpe/Return were not computed from one
   portfolio equity curve.

Independent of any corrected proxy:

- `ECONOMIC_GATE_OPENED=false`
- `PROMOTION_ELIGIBLE=false`
- No economic promotion claim is authorized.

### Corrected reporting snapshot

- GROSS_PNL=`{result["gross_pnl"]}`
- FEES_TOTAL=`{result["fees_total"]}`
- SLIPPAGE_TOTAL=`{result["slippage_total"]}`
- NET_PNL=`{result["net_pnl"]}`
- COST_DRAG=`{result["cost_drag"]}`
- NET_RETURN (corrected equal-capital proxy)=`{result["net_return_equal_capital_panel"]}`
- NET_RETURN (prior invalid sum)=`{result["prior_net_return_sum_instrument_returns"]}`
- SHARPE (corrected)=`{result["sharpe_corrected"]}`
- LEDGER_RECONCILIATION=`{result["ledger_reconciliation"]}`
- COST_APPLICATION=`{result["cost_application"]}`
- CAPITAL_DOUBLE_COUNTING=`{result["capital_double_counting"]}`
"""
    (EVIDENCE / "metrics_integrity_verdict.md").write_text(verdict, encoding="utf-8")

    # Corrected baseline metrics overlay (keeps prior fields for forensics).
    corrected = {
        **result,
        "status": "FAIL",
        "prior_baseline_metrics_forensics": {
            "net_return": result["prior_net_return_sum_instrument_returns"],
            "sharpe": result["sharpe_prior_cross_sectional"],
            "max_drawdown": result["max_drawdown_prior_worst_instrument"],
            "cost_drag": 0.0,
            "slippage_drag_invalid_unit": result["prior_fake_slippage_drag_bps_trades_unit"],
            "economic_class_prior": "INCONCLUSIVE_UNSTABLE",
        },
        # Canonical corrected exports used by closeout:
        "net_return": result["net_return_equal_capital_panel"],
        "sharpe": result["sharpe_corrected"],
        "profit_factor": result["profit_factor_trade_gross"],
        "max_drawdown": NA,
        "fees": result["fees_total"],
        "slippage_drag": result["slippage_total"],
    }
    (EVIDENCE / "baseline_metrics_corrected.json").write_text(
        json.dumps(corrected, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    # Update baseline_metrics.json in place with corrected truth + forensic prior.
    baseline_path = EVIDENCE / "baseline_metrics.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline.update(
        {
            "status": "FAIL",
            "economic_class": "INVALID_ECONOMIC_MEASUREMENT",
            "economic_measurement_valid": False,
            "cost_application": result["cost_application"],
            "capital_double_counting": True,
            "ledger_reconciliation": result["ledger_reconciliation"],
            "equity_reconciliation": result["equity_reconciliation"],
            "gross_pnl": result["gross_pnl"],
            "net_pnl": result["net_pnl"],
            "fees": result["fees_total"],
            "slippage_drag": result["slippage_total"],
            "cost_drag": result["cost_drag"],
            "net_return": result["net_return_equal_capital_panel"],
            "net_return_definition": result["net_return_definition"],
            "net_return_prior_invalid_sum_instrument_returns": result[
                "prior_net_return_sum_instrument_returns"
            ],
            "profit_factor": result["profit_factor_trade_gross"],
            "sharpe": result["sharpe_corrected"],
            "sharpe_definition": result["sharpe_definition"],
            "sharpe_prior_invalid_cross_sectional": result["sharpe_prior_cross_sectional"],
            "max_drawdown": NA,
            "max_drawdown_prior_worst_instrument": result["max_drawdown_prior_worst_instrument"],
            "portfolio_aggregation": result["portfolio_aggregation"],
            "initial_capital_per_instrument": INITIAL_CAPITAL_PER_INSTRUMENT,
            "ECONOMIC_GATE_OPENED": False,
            "PROMOTION_ELIGIBLE": False,
            "rationale": (
                "INVALID_ECONOMIC_MEASUREMENT: costs NOT_APPLIED in ledger; "
                "prior NET_RETURN summed independent instrument returns; "
                "no single portfolio equity for Sharpe/DD"
            ),
            "first_loss_boundaries": result["first_loss_boundaries"],
        }
    )
    baseline_path.write_text(
        json.dumps(baseline, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    (EVIDENCE / "metrics_integrity_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    # Refresh human verdict/robustness headers to fail-closed measurement invalid.
    (EVIDENCE / "verdict.md").write_text(verdict, encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                **{
                    k: result[k]
                    for k in [
                        "total_trades",
                        "gross_pnl",
                        "fees_total",
                        "slippage_total",
                        "net_pnl",
                        "cost_drag",
                        "cost_application",
                        "net_return_equal_capital_panel",
                        "prior_net_return_sum_instrument_returns",
                        "capital_double_counting",
                        "economic_class",
                        "economic_measurement_valid",
                        "ledger_reconciliation",
                    ]
                },
            },
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
