"""Single-run HOLDOUT panel evaluation: baseline vs ADX DI direction-confirmation eligibility gate.

Exactly one preregistered, execution-gated run against the sealed FINAL_AUDIT
holdout panel. Reuses the DEVELOPMENT package's filter/gate/backtest-wiring
code read-only (no retune); only the panel loader and preregistration
binding differ from the development evaluation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
import sys
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
from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v1.decision_v1 import (
    decide_development_evaluation,
)
from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v1.holdout_panel_bars_v1 import (
    included_panel_members,
    load_member_bars,
    resolve_holdout_archive_root,
    verify_holdout_panel_hashes,
)

# Filter / gate code is intentionally NOT copied: the holdout evaluation
# reuses the DEVELOPMENT package's frozen eligibility filter and gate
# read-only (identical treatment, no retune).
from src.research.adx_di_direction_confirmation_mr_eligibility_development_evaluation_v1.entry_eligibility_gate_v1 import (
    apply_eligibility_to_mapped_position_signal,
)
from src.research.adx_di_direction_confirmation_mr_eligibility_development_evaluation_v1.adx_di_direction_confirmation_eligibility_filter_v1 import (
    REQUIRED_FROZEN,
    assert_frozen_parameters_match_contract,
    compute_plus_minus_di,
    formula_freeze_payload,
    is_entry_eligible,
    long_eligible_mask_from_bars,
    short_eligible_mask_from_bars,
)
from src.research.adx_di_direction_confirmation_mr_eligibility_holdout_preregistration_v1 import (
    CONTRACT_REL_PATH,
    assert_execution_go_present,
    canonical_json_sha256,
    load_and_validate_repo_holdout_contract,
    load_json,
    preflight_holdout_execution_gates,
)

# Read-only reuse of the prior (failed regime_gated) evaluation's shared
# portfolio equity aggregation helper. This module is imported ONLY; the
# regime_gated_standaside_mr_development_evaluation_v1 package files are not
# mutated by this evaluation.
from src.research.regime_gated_standaside_mr_development_evaluation_v1.shared_portfolio_equity_research_v1 import (
    PORTFOLIO_AGGREGATION_ID,
    build_equal_weight_portfolio_equity,
    peak_gross_exposure_from_scaled_trades,
    portfolio_metrics_from_equity,
)

SLEEVE_INITIAL_CASH = 10_000.0
SHARED_INITIAL_CAPITAL = 10_000.0
STOP_PCT = 0.025
FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
HALF_SPREAD_BPS = 5.0
STRATEGY_ID = "bollinger_bands"
CONFIG_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
EVALUATION_RUN_ID = "evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1"


@dataclass(frozen=True)
class ArmResult:
    arm: str
    rows: list[dict[str, Any]]
    metrics: dict[str, Any]
    eligibility_attribution: dict[str, Any]
    wallclock_seconds: float


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_base_sha(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        sha = out.stdout.strip()
        return sha or None
    except Exception:  # noqa: BLE001
        return None


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
    # Preregistered cost / seed / stop semantics (identical to development).
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
def _optional_treatment_entry_eligibility_gate(
    *, enabled: bool, bars: pd.DataFrame | None
) -> Iterator[dict[str, int]]:
    """Research-local post-map side-aware entry-eligibility gate (no MV2/authority mutation).

    Identical mechanism to the DEVELOPMENT evaluation's gate (see that
    package's ``panel_runner_v1`` for the full rationale): wraps
    ``map_decision_evidence_to_position_signal_v1`` to apply the frozen,
    side-aware DI direction-confirmation rule (``is_entry_eligible``) to the
    mapped MV2 position signal. Mapped ``0`` (flat/exit) always passes
    through unchanged.
    """
    counters = {"entries_blocked_by_gate": 0}
    if not enabled:
        yield counters
        return
    if bars is None:
        raise ValueError("ELIGIBILITY_GATE_BARS_REQUIRED")

    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    plus_di_s, minus_di_s = compute_plus_minus_di(bars)
    warmup_bars = int(REQUIRED_FROZEN["warmup_bars"])
    warmup_mask = pd.Series(False, index=bars.index)
    n_warmup = min(warmup_bars, len(warmup_mask))
    if n_warmup > 0:
        warmup_mask.iloc[:n_warmup] = True
    state: dict[str, Any] = {"current_ts": None}

    original_bind_bar = wiring_mod.bind_bar_for_mv2_wiring_v1
    original_bind_warmup = wiring_mod._bind_economic_research_warmup_observation_bar_v1
    original_map = wiring_mod.map_decision_evidence_to_position_signal_v1

    def _bind_bar_tracked(**kwargs):  # type: ignore[no-untyped-def]
        state["current_ts"] = pd.Timestamp(kwargs["bar"].name)
        return original_bind_bar(**kwargs)

    def _bind_warmup_tracked(**kwargs):  # type: ignore[no-untyped-def]
        state["current_ts"] = pd.Timestamp(kwargs["bar"].name)
        return original_bind_warmup(**kwargs)

    def _map_gated(evidence):  # type: ignore[no-untyped-def]
        raw_signal = original_map(evidence)
        ts = state["current_ts"]
        if ts is None or len(plus_di_s) == 0:
            eligible = False
        else:
            plus_val = plus_di_s.asof(ts)
            minus_val = minus_di_s.asof(ts)
            in_warmup = bool(warmup_mask.asof(ts)) if len(warmup_mask) else True
            plus_f = float(plus_val) if pd.notna(plus_val) else float("nan")
            minus_f = float(minus_val) if pd.notna(minus_val) else float("nan")
            eligible = is_entry_eligible(
                signal=raw_signal, plus_di=plus_f, minus_di=minus_f, in_warmup=in_warmup
            )
        gated_signal = apply_eligibility_to_mapped_position_signal(raw_signal, eligible)
        if gated_signal != raw_signal:
            counters["entries_blocked_by_gate"] += 1
        return gated_signal

    wiring_mod.bind_bar_for_mv2_wiring_v1 = _bind_bar_tracked  # type: ignore[assignment]
    wiring_mod._bind_economic_research_warmup_observation_bar_v1 = (  # type: ignore[assignment]
        _bind_warmup_tracked
    )
    wiring_mod.map_decision_evidence_to_position_signal_v1 = _map_gated  # type: ignore[assignment]
    try:
        yield counters
    finally:
        wiring_mod.bind_bar_for_mv2_wiring_v1 = original_bind_bar  # type: ignore[assignment]
        wiring_mod._bind_economic_research_warmup_observation_bar_v1 = (  # type: ignore[assignment]
            original_bind_warmup
        )
        wiring_mod.map_decision_evidence_to_position_signal_v1 = original_map  # type: ignore[assignment]


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


def _entry_ts(rec: Mapping[str, Any]) -> pd.Timestamp:
    et = pd.Timestamp(rec["entry_time"])
    if et.tzinfo is None:
        et = et.tz_localize("UTC")
    else:
        et = et.tz_convert("UTC")
    return et


def _extract_member_economics(
    result: Any,
    *,
    member_id: str,
    decision_start: pd.Timestamp,
    decision_end: pd.Timestamp,
    long_eligible_mask: pd.Series,
    short_eligible_mask: pd.Series,
    entries_blocked_by_gate: int = 0,
) -> dict[str, Any]:
    bt = result.backtest_result
    trades_df = getattr(bt, "trades", None)
    trade_records: list[dict[str, Any]] = []
    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trade_records = trades_df.to_dict(orient="records")

    # Decision-segment filter: entry inside [start, end). For the holdout run
    # this is the full sealed panel, so the filter is a no-op safety check.
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

    equity = getattr(bt, "equity_curve", None)
    if equity is None or len(equity) == 0:
        raise ValueError(f"MISSING_EQUITY:{member_id}")
    eq = equity.astype(float)
    eq.index = pd.to_datetime(eq.index, utc=True)
    eq_dec = eq[(eq.index >= decision_start) & (eq.index < decision_end)]
    if eq_dec.empty:
        pre = eq[eq.index < decision_start]
        start_val = float(pre.iloc[-1]) if len(pre) else SLEEVE_INITIAL_CASH
        eq_dec = pd.Series(
            [start_val, start_val],
            index=pd.DatetimeIndex([decision_start, decision_end - pd.Timedelta(hours=1)]),
        )

    # ADX DI direction-confirmation eligibility attribution on the decision
    # segment. INFORMATIONAL ONLY (see development panel_runner_v1 for the
    # full rationale); the primary divergence proof is
    # ``entries_blocked_by_gate`` from the engine-effective monkeypatch below.
    combined_mask = (long_eligible_mask | short_eligible_mask).astype(bool)
    mask_dec = combined_mask.reindex(eq_dec.index).fillna(False)
    eligible_bar_share = float(mask_dec.mean()) if len(mask_dec) else 0.0
    entries_eligible = 0
    entries_on_ineligible_mask_bars = 0
    for r in filtered:
        et = _entry_ts(r)
        side = _classify_side(r)
        if side == "short":
            elig = bool(short_eligible_mask.asof(et)) if len(short_eligible_mask) else False
        elif side == "long":
            elig = bool(long_eligible_mask.asof(et)) if len(long_eligible_mask) else False
        else:
            elig = bool(combined_mask.asof(et)) if len(combined_mask) else False
        if elig:
            entries_eligible += 1
        else:
            entries_on_ineligible_mask_bars += 1

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
        "eligible_bar_share": eligible_bar_share,
        "entries_eligible": entries_eligible,
        "entries_on_ineligible_mask_bars": entries_on_ineligible_mask_bars,
        "entries_blocked_by_gate": int(entries_blocked_by_gate),
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
    sleeve_gross_rets = [float(r["gross_pnl"]) / SLEEVE_INITIAL_CASH for r in rows]
    gross_return = float(sum(sleeve_gross_rets) / len(sleeve_gross_rets)) if rows else 0.0
    eligible_shares = [float(r["eligible_bar_share"]) for r in rows]
    entries_eligible_total = int(sum(int(r["entries_eligible"]) for r in rows))
    entries_on_ineligible_mask_bars_total = int(
        sum(int(r["entries_on_ineligible_mask_bars"]) for r in rows)
    )
    entries_blocked_by_gate_total = int(sum(int(r["entries_blocked_by_gate"]) for r in rows))
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
        "mean_eligible_bar_share": float(sum(eligible_shares) / len(eligible_shares))
        if eligible_shares
        else 0.0,
        "entries_eligible": entries_eligible_total,
        "entries_on_ineligible_mask_bars": entries_on_ineligible_mask_bars_total,
        "entries_blocked_by_gate": entries_blocked_by_gate_total,
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
    for i, member in enumerate(members, start=1):
        canon = member["canonical_instrument_id"]
        bars = load_member_bars(
            archive_root,
            canonical_instrument_id=canon,
            start_inclusive=load_start,
            end_exclusive=decision_end,
        )
        long_mask = long_eligible_mask_from_bars(bars)
        short_mask = short_eligible_mask_from_bars(bars)
        # Gate context is per-instrument (bound to this member's bars) because
        # run_arm loops members and DI series must match the bars currently
        # being replayed by run_mv2_research_backtest_wiring_v1 below.
        with _optional_treatment_entry_eligibility_gate(enabled=gate, bars=bars) as counters:
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
            long_eligible_mask=long_mask,
            short_eligible_mask=short_mask,
            entries_blocked_by_gate=counters["entries_blocked_by_gate"],
        )
        rows.append(econ)
        print(
            json.dumps(
                {
                    "phase": arm,
                    "i": i,
                    "n": len(members),
                    "member": canon,
                    "trades": econ["trade_count"],
                    "entries_blocked_by_gate": econ["entries_blocked_by_gate"],
                }
            ),
            flush=True,
        )
    metrics = _aggregate_arm(rows)
    n_divergent_members = sum(1 for r in rows if int(r["entries_on_ineligible_mask_bars"]) > 0)
    n_gate_blocked_members = sum(1 for r in rows if int(r["entries_blocked_by_gate"]) > 0)
    eligibility_attr = {
        "mean_eligible_bar_share": metrics["mean_eligible_bar_share"],
        "entries_eligible": metrics["entries_eligible"],
        "entries_on_ineligible_mask_bars": metrics["entries_on_ineligible_mask_bars"],
        "entries_blocked_by_gate": metrics["entries_blocked_by_gate"],
        "instruments_with_divergence_count": n_divergent_members,
        "instruments_with_gate_blocked_entries_count": n_gate_blocked_members,
        "eligibility_gate_enabled": gate,
    }
    return ArmResult(
        arm=arm,
        rows=rows,
        metrics=metrics,
        eligibility_attribution=eligibility_attr,
        wallclock_seconds=float(time.perf_counter() - t0),
    )


def run_holdout_evaluation(
    *,
    output_dir: Path,
    archive_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gate 1: definition-only contract validation (requires holdout_run_count
    # == 0); does NOT by itself authorize execution or data access.
    load_and_validate_repo_holdout_contract(repo)
    contract = load_json(repo / CONTRACT_REL_PATH)

    # Gate 2: separate explicit operator GO env var required for execution.
    assert_execution_go_present()

    # Gate 3: preflight — frozen preregistration/split digests, single-run
    # budget, and development PASS binding re-verified against exact
    # expected constants BEFORE any sealed holdout data access.
    preflight = preflight_holdout_execution_gates(contract)
    holdout_run_count_before = int(preflight["holdout_run_count_before"])

    assert_frozen_parameters_match_contract(contract)
    freeze = formula_freeze_payload()
    (output_dir / "eligibility_filter_formula_freeze.json").write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    root = resolve_holdout_archive_root(archive_root)
    panel_proof = verify_holdout_panel_hashes(root)
    members = included_panel_members(root)
    seed = int(contract["seeds"]["primary_seed"])
    cfg = load_runtime_cfg(repo, seed=seed)

    # Decision segment: the FULL sealed holdout panel per contract
    # ``common_panel_bounds`` (NOT a development-style
    # ``final_development_confirmation`` sub-segment). The sealed holdout
    # archive contains exactly this bound period; there is no earlier data
    # to load as a separate warmup window, so the load window equals the
    # decision segment itself (the eligibility filter's own
    # ``warmup_bars=28`` mask absorbs the first bars in-place).
    panel_bounds = contract["common_panel_bounds"]
    decision_start = str(panel_bounds["start"])
    decision_end = str(panel_bounds["end_exclusive"])
    load_start = decision_start

    # EXACTLY one evaluation: baseline (control, unfiltered) then treatment
    # (ADX DI direction-confirmation side-aware eligibility gated) — two
    # arms, one holdout run.
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

    # Gate-effective divergence proof (PRIMARY): the monkeypatch counter of
    # mapped +-1 -> 0 signal overrides on the treatment arm.
    entries_blocked_by_gate = int(treatment.metrics["entries_blocked_by_gate"])
    gate_blocked_members = [
        r["member_id"] for r in treatment.rows if int(r["entries_blocked_by_gate"]) > 0
    ]

    baseline_entry_times = {
        r["member_id"]: sorted(str(t["entry_time"]) for t in (r.get("_trades_compact") or []))
        for r in baseline.rows
    }
    treatment_entry_times = {
        r["member_id"]: sorted(str(t["entry_time"]) for t in (r.get("_trades_compact") or []))
        for r in treatment.rows
    }
    members_with_entry_time_divergence = sorted(
        m
        for m in baseline_entry_times
        if baseline_entry_times.get(m) != treatment_entry_times.get(m)
    )
    entry_times_differ = len(members_with_entry_time_divergence) > 0
    trade_count_differs = int(treatment.metrics["trade_count"]) != int(
        baseline.metrics["trade_count"]
    )

    # INFORMATIONAL ONLY (see development panel_runner_v1 for rationale).
    baseline_entries_on_ineligible_mask_bars = sum(
        int(r["entries_on_ineligible_mask_bars"]) for r in baseline.rows
    )
    informational_divergent_members = [
        r["member_id"] for r in baseline.rows if int(r["entries_on_ineligible_mask_bars"]) > 0
    ]

    entry_eligibility_divergence_observed = (
        entries_blocked_by_gate > 0 or trade_count_differs or entry_times_differ
    )

    if (
        entries_blocked_by_gate == 0
        and baseline_entries_on_ineligible_mask_bars > 0
        and not trade_count_differs
        and not entry_times_differ
    ):
        raise RuntimeError("ENTRY_ELIGIBILITY_GATE_INEFFECTIVE")

    entry_candidates_control = sum(int(r["trade_count"]) for r in baseline.rows)
    eligible_entry_decisions = sum(int(r["entries_eligible"]) for r in treatment.rows)
    ineligible_entry_decisions = sum(
        int(r["entries_on_ineligible_mask_bars"]) for r in treatment.rows
    )
    bar_shares = [float(r["eligible_bar_share"]) for r in baseline.rows]
    bars_true_share = float(sum(bar_shares) / len(bar_shares)) if bar_shares else 0.0
    eligibility_attribution = {
        "entry_candidates_control": entry_candidates_control,
        "entries_suppressed": entries_blocked_by_gate,
        "entries_blocked_by_gate": entries_blocked_by_gate,
        "eligible_entry_decisions": eligible_entry_decisions,
        "ineligible_entry_decisions": ineligible_entry_decisions,
        "bars_with_eligibility_true_share": bars_true_share,
        "bars_with_eligibility_false_share": float(1.0 - bars_true_share),
        "instruments_with_gate_blocked_entries_count": len(gate_blocked_members),
        "instruments_with_gate_blocked_entries": sorted(gate_blocked_members),
        "trade_count_differs": trade_count_differs,
        "entry_times_differ": entry_times_differ,
        "members_with_entry_time_divergence": members_with_entry_time_divergence,
        "entry_eligibility_divergence_observed": entry_eligibility_divergence_observed,
        "baseline_entries_on_ineligible_mask_bars": baseline_entries_on_ineligible_mask_bars,
        "informational_instruments_with_ineligible_mask_bar_entries_count": len(
            informational_divergent_members
        ),
        "informational_instruments_with_ineligible_mask_bar_entries": sorted(
            informational_divergent_members
        ),
        "baseline": baseline.eligibility_attribution,
        "treatment": treatment.eligibility_attribution,
    }
    (output_dir / "eligibility_attribution.json").write_text(
        json.dumps(eligibility_attribution, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    thr = contract["decision_thresholds"]
    decision_out = decide_development_evaluation(
        baseline=baseline.metrics,
        treatment=treatment.metrics,
        entry_eligibility_divergence_observed=entry_eligibility_divergence_observed,
        minimum_trade_count=int(thr["minimum_trade_count"]),
        max_trade_count_reduction_fraction=float(
            thr["max_trade_count_reduction_fraction_vs_control"]
        ),
        cost_drag_fully_included=True,
    )

    def _public_metrics(m: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in m.items() if not str(k).startswith("_")}

    def _public_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            out.append({k: v for k, v in r.items() if not str(k).startswith("_")})
        return out

    # NOTE: portfolio equity CSVs are deliberately NOT written to the
    # committed evidence pack (matching the final DEVELOPMENT evidence pack,
    # which also does not track them). The in-memory portfolio equity series
    # is only used internally above for aggregate metrics.

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

    config_snapshot = {
        "schema_version": "evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_config_snapshot.v1",
        "hypothesis_id": contract["hypothesis_id"],
        "contract_id": contract["schema_version"],
        "baseline_config_id": CONFIG_ID,
        "treatment_id": contract["treatment"]["treatment_id"],
        "dataset_id": panel_proof["dataset_id"],
        "decision_segment": {
            "start": decision_start,
            "end_exclusive": decision_end,
        },
        "decision_thresholds": thr,
        "cost_model": contract["cost_model"],
        "seed": seed,
        "stop_pct": STOP_PCT,
        "feature_formula_sha256": freeze["feature_formula_sha256"],
    }
    (output_dir / "config_snapshot.json").write_text(
        json.dumps(config_snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    code_hashes = {
        "adx_di_direction_confirmation_eligibility_filter_v1.py": _sha256_file(
            repo
            / "src/research/adx_di_direction_confirmation_mr_eligibility_development_evaluation_v1"
            / "adx_di_direction_confirmation_eligibility_filter_v1.py"
        ),
        "holdout_panel_bars_v1.py": _sha256_file(
            repo
            / "src/research/adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v1"
            / "holdout_panel_bars_v1.py"
        ),
        "panel_runner_v1.py": _sha256_file(
            repo
            / "src/research/adx_di_direction_confirmation_mr_eligibility_holdout_evaluation_v1"
            / "panel_runner_v1.py"
        ),
        "contract": canonical_json_sha256(contract),
        "feature_formula_sha256": freeze["feature_formula_sha256"],
    }
    (output_dir / "code_config_hashes.json").write_text(
        json.dumps(code_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    command = (
        "PYTHONPATH=src:. PEAK_TRADE_ADX_DI_HOLDOUT_EXECUTION_GO=true python3 scripts/research/"
        "run_evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1.py "
        f"--output-dir {output_dir}"
    )
    base_sha = _git_base_sha(repo)
    holdout_run_count_after = holdout_run_count_before + 1
    summary = {
        "schema_version": "evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_summary.v1",
        "evaluation_run_id": EVALUATION_RUN_ID,
        "backtest_executed": True,
        "hypothesis_id": contract["hypothesis_id"],
        "contract_id": contract["schema_version"],
        "contract_ref": CONTRACT_REL_PATH,
        "config_id": CONFIG_ID,
        "dataset_id": panel_proof["dataset_id"],
        "dataset_class": "SEALED_HOLDOUT_FINAL_AUDIT_ONLY",
        "holdout_accessed": True,
        "sealed_holdout_content_inspected": True,
        "holdout_period": f"{decision_start}..{decision_end}",
        "decision_segment_note": (
            "The FULL sealed holdout panel (contract common_panel_bounds) is the "
            "decision segment per splits.decision_segment == "
            "'full_sealed_holdout_panel'; there is no separate holdout "
            "train/validation split (chronological train/validation is forbidden "
            "on the holdout by the preregistration contract)."
        ),
        "instrument_count": len(members),
        "seed": seed,
        "cost_model": contract["cost_model"],
        "stop_pct": STOP_PCT,
        "command": command,
        "panel_proof": panel_proof,
        "feature_formula_sha256": freeze["feature_formula_sha256"],
        "filter_id": freeze["filter_id"],
        "baseline_metrics": _public_metrics(baseline.metrics),
        "treatment_metrics": _public_metrics(treatment.metrics),
        "deltas": {
            "net_return_abs": float(treatment.metrics["net_return"])
            - float(baseline.metrics["net_return"]),
            "trade_count_abs": int(treatment.metrics["trade_count"])
            - int(baseline.metrics["trade_count"]),
            "trade_count_relative": (
                float(treatment.metrics["trade_count"]) / float(baseline.metrics["trade_count"])
                - 1.0
                if baseline.metrics["trade_count"]
                else None
            ),
            "max_drawdown_abs": float(treatment.metrics["max_drawdown"])
            - float(baseline.metrics["max_drawdown"]),
        },
        "eligibility_attribution": eligibility_attribution,
        "decision": decision_out,
        "result_class": decision_out["result_class"],
        "baseline_wallclock_seconds": baseline.wallclock_seconds,
        "treatment_wallclock_seconds": treatment.wallclock_seconds,
        "holdout_run_count": holdout_run_count_after,
        "holdout_run_limit": int(preflight["holdout_run_limit"]),
        "holdout_run_count_before": holdout_run_count_before,
        "holdout_split_digest": preflight["holdout_split_digest"],
        "holdout_preregistration_digest": preflight["holdout_preregistration_digest"],
        "development_binding": contract["development_binding"],
        "productive_trading_logic_changed": False,
        "authority_changed": False,
        "economic_validity_offline_gate_changed": False,
        "promotion_eligible": False,
        "runtime_activated": False,
        "shadow_activated": False,
        "testnet_activated": False,
        "orders_sent": False,
        "no_retry": True,
        "no_post_result_tuning": True,
        "operator_holdout_go": True,
        "base_sha": base_sha,
        "python_version": sys.version.split()[0],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )

    run_manifest = {
        "schema_version": "evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_run_manifest.v1",
        "base_sha": base_sha,
        "hypothesis_id": contract["hypothesis_id"],
        "evaluation_run_id": EVALUATION_RUN_ID,
        "result_class": decision_out["result_class"],
        "reason": decision_out["reason"],
        "seed": seed,
        "holdout_run_count": holdout_run_count_after,
        "holdout_run_limit": int(preflight["holdout_run_limit"]),
        "holdout_run_count_before": holdout_run_count_before,
        "holdout_split_digest": preflight["holdout_split_digest"],
        "holdout_preregistration_digest": preflight["holdout_preregistration_digest"],
        "holdout_accessed": True,
        "sealed_holdout_content_inspected": True,
        "promotion_eligible": False,
        "economic_validity_offline_gate_changed": False,
        "economic_gate_opened": False,
        "runtime_activated": False,
        "orders_sent": False,
        "evaluation_retried": False,
        "no_retry": True,
        "no_post_result_tuning": True,
        "baseline_trade_count": int(baseline.metrics["trade_count"]),
        "treatment_trade_count": int(treatment.metrics["trade_count"]),
        "baseline_profit_factor": baseline.metrics.get("profit_factor"),
        "treatment_profit_factor": treatment.metrics.get("profit_factor"),
        "entries_blocked_by_gate": entries_blocked_by_gate,
        "exit_code": 0,
        "exit_status": "COMPLETED",
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )

    _write_safety_attestation(output_dir, summary=summary, decision_out=decision_out)
    _write_readme(output_dir, summary=summary, decision_out=decision_out, command=command)

    return summary


def _write_safety_attestation(
    output_dir: Path, *, summary: Mapping[str, Any], decision_out: Mapping[str, Any]
) -> None:
    text = f"""# Safety attestation — evaluate ADX DI direction confirmation MR eligibility holdout v1

- `LIVE_AUTHORIZED=false`
- `RUNTIME_ACTIVATED=false`
- `SHADOW_ACTIVATED=false`
- `TESTNET_ACTIVATED=false`
- `ORDERS_SENT=false`
- `HOLDOUT_ACCESSED=true`
- `SEALED_HOLDOUT_CONTENT_INSPECTED=true`
- `PRODUCTIVE_TRADING_LOGIC_CHANGED=false`
- `AUTHORITY_CHANGED=false`
- `ECONOMIC_VALIDITY_OFFLINE_GATE_CHANGED=false`
- `ECONOMIC_GATE_OPENED=false`
- `PROMOTION_ELIGIBLE=false`
- `EVALUATION_EXECUTED=true`
- `HOLDOUT_RUN_COUNT={summary["holdout_run_count"]}`
- `HOLDOUT_RUN_LIMIT={summary["holdout_run_limit"]}`
- `HOLDOUT_RUN_COUNT_BEFORE={summary["holdout_run_count_before"]}`
- `EVALUATION_RETRIED=false`
- `NO_RETRY=true`
- `NO_POST_RESULT_TUNING=true`
- `RESULT_CLASS={decision_out["result_class"]}`
- Exactly one preregistered, execution-gated holdout run of the already
  terminal DEVELOPMENT PASS of
  `ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1`.
  No runtime/orders, no productive Master-V2/Double-Play/risk/sizing/execution
  mutation. This holdout result does not open the economic offline gate and
  does not activate any strategy/runtime regardless of `RESULT_CLASS`.
"""
    (output_dir / "safety_attestation.md").write_text(text, encoding="utf-8")


def _write_readme(
    output_dir: Path,
    *,
    summary: Mapping[str, Any],
    decision_out: Mapping[str, Any],
    command: str,
) -> None:
    baseline = summary["baseline_metrics"]
    treatment = summary["treatment_metrics"]
    text = f"""# Evaluate ADX DI direction confirmation MR eligibility holdout v1

```text
SLICE=EVALUATE_ADX_DI_DIRECTION_CONFIRMATION_MR_ELIGIBILITY_HOLDOUT_V1
BASE_SHA={summary["base_sha"]}
HYPOTHESIS={summary["hypothesis_id"]}
RESULT_CLASS={decision_out["result_class"]}
REASON={decision_out["reason"]}
HOLDOUT_RUN_COUNT={summary["holdout_run_count"]}
HOLDOUT_RUN_LIMIT={summary["holdout_run_limit"]}
DATASET={summary["dataset_id"]}
DATASET_CLASS={summary["dataset_class"]}
HOLDOUT_ACCESSED=true
SEALED_HOLDOUT_CONTENT_INSPECTED=true
PROMOTION_ELIGIBLE=false
ECONOMIC_VALIDITY_OFFLINE_GATE_CHANGED=false
RUNTIME_ACTIVATED=false
ORDERS_SENT=false
NO_POST_RESULT_TUNING=true
NO_RETRY=true
OPERATOR_HOLDOUT_GO=true
```

## Result (mechanical)

- Control trades: `{baseline["trade_count"]}` -> Treatment trades: `{treatment["trade_count"]}`
- Control net PF: `{baseline.get("profit_factor")}` -> Treatment net PF: `{treatment.get("profit_factor")}`
- Control net return: `{baseline.get("net_return")}` -> Treatment: `{treatment.get("net_return")}`
- Control max DD: `{baseline.get("max_drawdown")}` -> Treatment: `{treatment.get("max_drawdown")}`
- `entries_blocked_by_gate` (treatment): `{treatment.get("entries_blocked_by_gate")}`
- Divergence observed: `{summary["eligibility_attribution"]["entry_eligibility_divergence_observed"]}`

This is the single preregistered, execution-gated holdout run
(`holdout_run_limit=1`, `holdout_run_count_before=0`). The result is terminal:
no retry, no post-result tuning, no reopening without a new hypothesis id.
The economic offline gate remains closed and no runtime/orders are affected
regardless of `RESULT_CLASS`.

## Command (single authorized run)

```bash
PYTHONPATH=src:. PEAK_TRADE_ADX_DI_HOLDOUT_EXECUTION_GO=true python3 scripts/research/run_evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1.py \\
  --output-dir docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_holdout_v1
```
"""
    (output_dir / "README.md").write_text(text, encoding="utf-8")


__all__ = ["run_holdout_evaluation", "EVALUATION_RUN_ID", "CONFIG_ID"]
