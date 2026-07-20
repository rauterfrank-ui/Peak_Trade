"""Single-run DEVELOPMENT panel evaluation: baseline vs regime-gated standaside."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

import pandas as pd

from src.backtest.admissible_versioned_futures_dataset_v1 import (
    DatasetProfileBindingV1,
    DatasetProfileV1,
    ExecutionCostBindingV1,
    L1ObservationStatusV1,
)
from src.backtest.mv2_research_wiring_v1 import (
    compute_mv2_backtest_metrics_v1,
    run_mv2_research_backtest_wiring_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.decision_v1 import (
    decide_development_evaluation,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.dev_panel_bars_v1 import (
    included_panel_members,
    load_member_bars,
    resolve_development_archive_root,
    verify_development_panel_hashes,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.entry_eligibility_gate_v1 import (
    execute_gated_configured_strategy_signal_series_v1,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.regime_features_v1 import (
    REGIME_RANGE,
    assert_thresholds_match_contract,
    formula_freeze_payload,
    regime_labels_from_close,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.shared_portfolio_equity_research_v1 import (
    PORTFOLIO_AGGREGATION_ID,
    build_equal_weight_portfolio_equity,
    peak_gross_exposure_from_scaled_trades,
    portfolio_metrics_from_equity,
)
from src.research.regime_gated_standaside_mr_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    canonical_json_sha256,
    load_json,
    load_and_validate_repo_contract,
)

SLEEVE_INITIAL_CASH = 10_000.0
SHARED_INITIAL_CAPITAL = 10_000.0
STOP_PCT = 0.025
FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
HALF_SPREAD_BPS = 5.0
STRATEGY_ID = "bollinger_bands"
CONFIG_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
EVALUATION_RUN_ID = "evaluate_regime_gated_standaside_mr_development_v1"


@dataclass(frozen=True)
class ArmResult:
    arm: str
    rows: list[dict[str, Any]]
    metrics: dict[str, Any]
    regime_attribution: dict[str, Any]
    wallclock_seconds: float


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _profile() -> DatasetProfileBindingV1:
    return DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=HALF_SPREAD_BPS,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )


def load_runtime_cfg(repo: Path, *, seed: int) -> dict[str, Any]:
    src = Path(
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z/"
        "runtime_evaluation_config.json"
    )
    cfg = json.loads(src.read_text(encoding="utf-8"))
    cfg = copy.deepcopy(cfg)
    # Preregistered cost / seed / stop semantics.
    cfg["backtest"]["fee_bps"] = FEE_BPS
    cfg["backtest"]["slippage_bps"] = SLIPPAGE_BPS
    cfg["backtest"]["economic_research_execution_cost"]["fee_bps"] = FEE_BPS
    cfg["backtest"]["economic_research_execution_cost"]["slippage_bps"] = SLIPPAGE_BPS
    cfg["backtest"]["economic_research_execution_cost"]["conservative_half_spread_bps"] = (
        HALF_SPREAD_BPS
    )
    cfg["backtest"]["dataset_admissibility"]["execution_cost_binding"][
        "conservative_half_spread_bps"
    ] = HALF_SPREAD_BPS
    cfg["economic_evaluation_v1"]["monte_carlo"]["seed"] = int(seed)
    cfg["offline_evaluation_sizing_contract_v1"]["stop_pct"] = STOP_PCT
    # Keep strategy params from immutable baseline binding.
    binding = load_json(repo / "config/research" / f"{CONFIG_ID}.json")
    params = binding["binding"]["parameter_binding"]
    cfg["economic_evaluation_v1"]["strategy_params"] = {
        "bb_period": params["bb_period"],
        "bb_std": params["bb_std"],
        "entry_threshold": params["entry_threshold"],
        "exit_threshold": params["exit_threshold"],
    }
    cfg["economic_evaluation_v1"]["strategy_id"] = STRATEGY_ID
    cfg["economic_evaluation_v1"]["strategy_version"] = "v2"
    return cfg


@contextmanager
def _optional_treatment_signal_gate(enabled: bool) -> Iterator[None]:
    if not enabled:
        yield
        return
    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    original = wiring_mod.execute_configured_strategy_signal_series_v1

    def _gated(bars, *, strategy_id, cfg):  # type: ignore[no-untyped-def]
        return execute_gated_configured_strategy_signal_series_v1(
            bars, strategy_id=strategy_id, cfg=cfg
        )

    wiring_mod.execute_configured_strategy_signal_series_v1 = _gated  # type: ignore[assignment]
    try:
        yield
    finally:
        wiring_mod.execute_configured_strategy_signal_series_v1 = original  # type: ignore[assignment]


def _classify_side(rec: Mapping[str, Any]) -> str:
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


def _extract_member_economics(
    result: Any,
    *,
    member_id: str,
    decision_start: pd.Timestamp,
    decision_end: pd.Timestamp,
    regime_labels: pd.Series,
) -> dict[str, Any]:
    bt = result.backtest_result
    trades_df = getattr(bt, "trades", None)
    trade_records: list[dict[str, Any]] = []
    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trade_records = trades_df.to_dict(orient="records")

    # Decision-segment filter: entry inside [start, end).
    filtered: list[dict[str, Any]] = []
    for rec in trade_records:
        et = rec.get("entry_time")
        if et is None:
            continue
        ets = pd.Timestamp(et)
        if ets.tzinfo is None:
            ets = ets.tz_localize("UTC")
        else:
            ets = ets.tz_convert("UTC")
        if decision_start <= ets < decision_end:
            filtered.append(rec)

    gross_pnls = [float(r["gross_pnl"]) for r in filtered if r.get("gross_pnl") is not None]
    net_pnls = [float(r["pnl"]) for r in filtered if r.get("pnl") is not None]
    fees = []
    slips = []
    for r in filtered:
        if r.get("fee_total") is not None:
            fees.append(float(r["fee_total"]))
        elif r.get("fee") is not None:
            fees.append(float(r["fee"]))
        if r.get("slippage_total") is not None:
            slips.append(float(r["slippage_total"]))

    long_n = sum(1 for r in filtered if _classify_side(r) == "long")
    short_n = sum(1 for r in filtered if _classify_side(r) == "short")
    wins = sum(1 for x in net_pnls if x > 0)
    win_rate = (wins / len(net_pnls)) if net_pnls else 0.0
    gross_pnl = float(sum(gross_pnls)) if gross_pnls else 0.0
    net_pnl = float(sum(net_pnls)) if net_pnls else 0.0
    fee_total = float(sum(fees)) if fees else 0.0
    slip_total = float(sum(slips)) if slips else 0.0
    cost_drag = float(gross_pnl - net_pnl)

    # Sleeve equity for shared book: use full curve, then slice to decision window.
    equity = getattr(bt, "equity_curve", None)
    if equity is None or len(equity) == 0:
        raise ValueError(f"MISSING_EQUITY:{member_id}")
    eq = equity.astype(float)
    eq.index = pd.to_datetime(eq.index, utc=True)
    eq_dec = eq[(eq.index >= decision_start) & (eq.index < decision_end)]
    if eq_dec.empty:
        # Fall back to last pre-segment equity carried into an empty stub.
        pre = eq[eq.index < decision_start]
        start_val = float(pre.iloc[-1]) if len(pre) else SLEEVE_INITIAL_CASH
        eq_dec = pd.Series(
            [start_val, start_val],
            index=pd.DatetimeIndex([decision_start, decision_end - pd.Timedelta(hours=1)]),
        )

    # Regime attribution on decision segment.
    labels = regime_labels.reindex(eq_dec.index).fillna("TREND_STRONG")
    range_share = float((labels == REGIME_RANGE).mean()) if len(labels) else 0.0
    entries_in_range = 0
    entries_standaside = 0
    for r in filtered:
        et = pd.Timestamp(r["entry_time"])
        if et.tzinfo is None:
            et = et.tz_localize("UTC")
        else:
            et = et.tz_convert("UTC")
        lab = regime_labels.asof(et) if len(regime_labels) else "TREND_STRONG"
        if lab == REGIME_RANGE:
            entries_in_range += 1
        else:
            entries_standaside += 1

    pf_net = None
    if net_pnls:
        wins_sum = float(sum(x for x in net_pnls if x > 0))
        loss_sum = float(sum(x for x in net_pnls if x < 0))
        if loss_sum < 0:
            pf_net = wins_sum / abs(loss_sum)
        elif wins_sum > 0:
            pf_net = float("inf")
        else:
            pf_net = None

    try:
        metrics = dict(compute_mv2_backtest_metrics_v1(bt))
    except Exception as exc:  # noqa: BLE001
        metrics = {"_metrics_error": str(exc)}

    return {
        "member_id": member_id,
        "trade_count": len(filtered),
        "long_trades": long_n,
        "short_trades": short_n,
        "gross_pnl": gross_pnl,
        "net_pnl": net_pnl,
        "fees": fee_total,
        "slippage": slip_total,
        "cost_drag": cost_drag,
        "win_rate": win_rate,
        "profit_factor_net": pf_net,
        "net_return_sleeve": float(eq_dec.iloc[-1] / eq_dec.iloc[0] - 1.0),
        "max_drawdown_sleeve_engine": metrics.get("max_drawdown"),
        "range_bound_bar_share": range_share,
        "entries_in_range": entries_in_range,
        "entries_outside_range_unexpected": entries_standaside,
        "_equity_decision": eq_dec,
        "_trades_compact": [
            {
                "side": _classify_side(r),
                "pnl": float(r["pnl"]) if r.get("pnl") is not None else None,
                "gross_pnl": float(r["gross_pnl"]) if r.get("gross_pnl") is not None else None,
                "entry_time": str(r.get("entry_time")),
                "exit_time": str(r.get("exit_time")),
                "size": float(r["size"]) if r.get("size") is not None else None,
                "entry_price": float(r["entry_price"])
                if r.get("entry_price") is not None
                else None,
            }
            for r in filtered
        ],
    }


def _aggregate_arm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    curves = {r["member_id"]: r["_equity_decision"] for r in rows}
    portfolio_eq = build_equal_weight_portfolio_equity(
        curves, initial_capital=SHARED_INITIAL_CAPITAL
    )
    port = portfolio_metrics_from_equity(portfolio_eq, initial_capital=SHARED_INITIAL_CAPITAL)
    all_trades: list[dict[str, Any]] = []
    for r in rows:
        all_trades.extend(r.get("_trades_compact") or [])
    exposure = peak_gross_exposure_from_scaled_trades(
        all_trades,
        n_instruments=len(rows),
        initial_capital=SHARED_INITIAL_CAPITAL,
        sleeve_initial_cash=SLEEVE_INITIAL_CASH,
    )
    trade_count = sum(int(r["trade_count"]) for r in rows)
    gross_pnl = float(sum(float(r["gross_pnl"]) for r in rows))
    net_pnl = float(sum(float(r["net_pnl"]) for r in rows))
    fees = float(sum(float(r["fees"]) for r in rows))
    slippage = float(sum(float(r["slippage"]) for r in rows))
    cost_drag = float(sum(float(r["cost_drag"]) for r in rows))
    long_n = sum(int(r["long_trades"]) for r in rows)
    short_n = sum(int(r["short_trades"]) for r in rows)
    net_trade_pnls = [float(t["pnl"]) for t in all_trades if t.get("pnl") is not None]
    wins = sum(1 for x in net_trade_pnls if x > 0)
    win_rate = (wins / len(net_trade_pnls)) if net_trade_pnls else 0.0
    wins_sum = float(sum(x for x in net_trade_pnls if x > 0))
    loss_sum = float(sum(x for x in net_trade_pnls if x < 0))
    if loss_sum < 0:
        pf = wins_sum / abs(loss_sum)
    elif wins_sum > 0:
        pf = float("inf")
    else:
        pf = 0.0
    # Gross return from mean sleeve gross; net return from shared book.
    sleeve_gross_rets = [float(r["gross_pnl"]) / SLEEVE_INITIAL_CASH for r in rows]
    gross_return = float(sum(sleeve_gross_rets) / len(sleeve_gross_rets)) if rows else 0.0
    range_shares = [float(r["range_bound_bar_share"]) for r in rows]
    return {
        "portfolio_aggregation_id": PORTFOLIO_AGGREGATION_ID,
        "initial_capital": SHARED_INITIAL_CAPITAL,
        "instrument_count": len(rows),
        "trade_count": trade_count,
        "long_trades": long_n,
        "short_trades": short_n,
        "gross_pnl": gross_pnl,
        "net_pnl": net_pnl,
        "fees": fees,
        "slippage": slippage,
        "cost_drag": cost_drag,
        "gross_return": gross_return,
        "net_return": float(port["net_return"]),
        "sharpe": float(port["sharpe"]),
        "max_drawdown": float(port["max_drawdown"]),
        "profit_factor": pf if math.isfinite(pf) else None,
        "win_rate": win_rate,
        "turnover": float(trade_count),
        "exposure_peak_gross": float(exposure["peak_gross_exposure"]),
        "capital_utilization": float(exposure["capital_utilization"]),
        "final_equity": float(port["final_equity"]),
        "mean_range_bound_bar_share": float(sum(range_shares) / len(range_shares))
        if range_shares
        else 0.0,
        "entries_in_range": int(sum(int(r["entries_in_range"]) for r in rows)),
        "entries_outside_range_unexpected": int(
            sum(int(r["entries_outside_range_unexpected"]) for r in rows)
        ),
        "_portfolio_equity": portfolio_eq,
    }


def run_arm(
    *,
    arm: str,
    cfg: dict[str, Any],
    archive_root: Path,
    members: list[dict[str, str]],
    load_start: str,
    decision_start: str,
    decision_end: str,
    gate: bool,
) -> ArmResult:
    t0 = time.perf_counter()
    d_start = pd.Timestamp(decision_start)
    d_end = pd.Timestamp(decision_end)
    rows: list[dict[str, Any]] = []
    with _optional_treatment_signal_gate(gate):
        for i, member in enumerate(members, start=1):
            native = member["native_instrument_id"]
            canon = member["canonical_instrument_id"]
            bars = load_member_bars(
                archive_root,
                native_instrument_id=native,
                start_inclusive=load_start,
                end_exclusive=decision_end,
            )
            labels = regime_labels_from_close(bars["close"])
            result = run_mv2_research_backtest_wiring_v1(
                bars,
                strategy_id=STRATEGY_ID,
                cfg=cfg,
                instrument_id=CANONICAL_INSTRUMENT_ID,
                profile_binding=_profile(),
                observational_panel_member_instrument_id=canon,
            )
            econ = _extract_member_economics(
                result,
                member_id=canon,
                decision_start=d_start,
                decision_end=d_end,
                regime_labels=labels,
            )
            rows.append(econ)
            print(
                json.dumps(
                    {
                        "phase": arm,
                        "i": i,
                        "n": len(members),
                        "member": native,
                        "trades": econ["trade_count"],
                    }
                ),
                flush=True,
            )
    metrics = _aggregate_arm(rows)
    regime_attr = {
        "mean_range_bound_bar_share": metrics["mean_range_bound_bar_share"],
        "entries_in_range": metrics["entries_in_range"],
        "entries_outside_range_unexpected": metrics["entries_outside_range_unexpected"],
        "standaside_gate_enabled": gate,
    }
    return ArmResult(
        arm=arm,
        rows=rows,
        metrics=metrics,
        regime_attribution=regime_attr,
        wallclock_seconds=float(time.perf_counter() - t0),
    )


def run_development_evaluation(
    *,
    output_dir: Path,
    archive_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    output_dir.mkdir(parents=True, exist_ok=True)
    load_and_validate_repo_contract(repo)
    contract = load_json(repo / CONTRACT_REL_PATH)
    assert_thresholds_match_contract(contract)
    freeze = formula_freeze_payload()
    (output_dir / "feature_formula_freeze.json").write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    root = resolve_development_archive_root(archive_root)
    panel_proof = verify_development_panel_hashes(root)
    members = included_panel_members(root)
    seed = int(contract["seeds"]["primary_seed"])
    cfg = load_runtime_cfg(repo, seed=seed)
    decision = contract["splits"]["final_development_confirmation"]
    decision_start = str(decision["start"])
    decision_end = str(decision["end_exclusive"])
    # Warmup: max feature lookback + bb period before decision start.
    load_start_ts = pd.Timestamp(decision_start) - pd.Timedelta(hours=168 + 20)
    load_start = load_start_ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    # EXACTLY one evaluation: baseline then treatment (two arms, one run).
    baseline = run_arm(
        arm="baseline",
        cfg=cfg,
        archive_root=root,
        members=members,
        load_start=load_start,
        decision_start=decision_start,
        decision_end=decision_end,
        gate=False,
    )
    treatment = run_arm(
        arm="treatment",
        cfg=cfg,
        archive_root=root,
        members=members,
        load_start=load_start,
        decision_start=decision_start,
        decision_end=decision_end,
        gate=True,
    )

    thr = contract["decision_thresholds"]
    decision_out = decide_development_evaluation(
        baseline=baseline.metrics,
        treatment=treatment.metrics,
        minimum_trade_count=int(thr["minimum_trade_count"]),
        materiality_epsilon_net_return_abs=float(thr["materiality_epsilon_net_return_abs"]),
    )

    def _public_metrics(m: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in m.items() if not str(k).startswith("_")}

    def _public_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            out.append({k: v for k, v in r.items() if not str(k).startswith("_")})
        return out

    # Persist portfolio equity paths.
    baseline.metrics["_portfolio_equity"].to_csv(output_dir / "portfolio_equity_baseline.csv")
    treatment.metrics["_portfolio_equity"].to_csv(output_dir / "portfolio_equity_treatment.csv")

    instrument_attribution = {
        "baseline": _public_rows(baseline.rows),
        "treatment": _public_rows(treatment.rows),
    }
    (output_dir / "instrument_attribution.json").write_text(
        json.dumps(instrument_attribution, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (output_dir / "baseline_metrics.json").write_text(
        json.dumps(_public_metrics(baseline.metrics), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "treatment_metrics.json").write_text(
        json.dumps(_public_metrics(treatment.metrics), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "comparison_decision.json").write_text(
        json.dumps(decision_out, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "regime_attribution.json").write_text(
        json.dumps(
            {
                "baseline": baseline.regime_attribution,
                "treatment": treatment.regime_attribution,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    code_hashes = {
        "regime_features_v1.py": _sha256_file(
            repo
            / "src/research/regime_gated_standaside_mr_development_evaluation_v1/regime_features_v1.py"
        ),
        "entry_eligibility_gate_v1.py": _sha256_file(
            repo
            / "src/research/regime_gated_standaside_mr_development_evaluation_v1/entry_eligibility_gate_v1.py"
        ),
        "panel_runner_v1.py": _sha256_file(
            repo
            / "src/research/regime_gated_standaside_mr_development_evaluation_v1/panel_runner_v1.py"
        ),
        "contract": canonical_json_sha256(contract),
        "feature_formula_sha256": freeze["feature_formula_sha256"],
    }
    (output_dir / "code_config_hashes.json").write_text(
        json.dumps(code_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    command = (
        "PYTHONPATH=src:. python3 scripts/research/"
        "run_evaluate_regime_gated_standaside_mr_development_v1.py "
        f"--output-dir {output_dir}"
    )
    summary = {
        "schema_version": "evaluate_regime_gated_standaside_mr_development_summary.v1",
        "evaluation_run_id": EVALUATION_RUN_ID,
        "evaluation_run_count": 1,
        "backtest_executed": True,
        "hypothesis_id": contract["hypothesis_id"],
        "contract_id": contract["schema_version"],
        "contract_ref": CONTRACT_REL_PATH,
        "config_id": CONFIG_ID,
        "dataset_id": panel_proof["dataset_id"],
        "dataset_class": "DEVELOPMENT_ONLY",
        "development_panel_accessed": True,
        "development_period": f"{decision_start}..{decision_end}",
        "instrument_count": len(members),
        "seed": seed,
        "cost_model": contract["cost_model"],
        "stop_pct": STOP_PCT,
        "command": command,
        "panel_proof": panel_proof,
        "feature_formula_sha256": freeze["feature_formula_sha256"],
        "baseline_metrics": _public_metrics(baseline.metrics),
        "treatment_metrics": _public_metrics(treatment.metrics),
        "decision": decision_out,
        "result_class": decision_out["result_class"],
        "baseline_wallclock_seconds": baseline.wallclock_seconds,
        "treatment_wallclock_seconds": treatment.wallclock_seconds,
        "holdout_accessed": False,
        "sealed_holdout_content_inspected": False,
        "productive_trading_logic_changed": False,
        "authority_changed": False,
        "economic_validity_offline_gate_changed": False,
        "promotion_eligible": False,
        "runtime_activated": False,
        "shadow_activated": False,
        "testnet_activated": False,
        "orders_sent": False,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return summary


__all__ = ["run_development_evaluation", "EVALUATION_RUN_ID", "CONFIG_ID"]
