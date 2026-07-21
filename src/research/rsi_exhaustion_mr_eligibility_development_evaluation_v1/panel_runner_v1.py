"""Single-run DEVELOPMENT panel evaluation: baseline vs RSI-exhaustion eligibility gate."""

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
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (
    included_panel_members,
    load_member_bars,
    resolve_development_archive_root,
    verify_development_panel_hashes,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.research.rsi_exhaustion_mr_eligibility_development_evaluation_v1.decision_v1 import (
    decide_development_evaluation,
)
from src.research.rsi_exhaustion_mr_eligibility_development_evaluation_v1.entry_eligibility_gate_v1 import (
    apply_eligibility_to_mapped_position_signal,
)
from src.research.rsi_exhaustion_mr_eligibility_development_evaluation_v1.rsi_exhaustion_eligibility_filter_v1 import (
    assert_frozen_parameters_match_contract,
    eligibility_mask_from_bars,
    formula_freeze_payload,
)
from src.research.rsi_exhaustion_mr_eligibility_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    canonical_json_sha256,
    load_and_validate_repo_contract,
    load_json,
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
EVALUATION_RUN_ID = "evaluate_rsi_exhaustion_mr_eligibility_development_v1"


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
def _optional_treatment_entry_eligibility_gate(
    *, enabled: bool, bars: pd.DataFrame | None
) -> Iterator[dict[str, int]]:
    """Research-local post-map entry-eligibility gate (no MV2/authority mutation).

    The MV2 replay engine trades on the mapped position signal produced by
    ``map_decision_evidence_to_position_signal_v1`` (called from
    ``run_mv2_research_backtest_wiring_v1``'s bar loop), NOT on the raw
    configured-strategy signal series. Monkeypatching the raw strategy
    signal series (the prior implementation) never reaches the engine's
    actual entry decision, so it had zero economic effect.

    This gate instead wraps ``map_decision_evidence_to_position_signal_v1``
    itself: it tracks the current bar timestamp (via wrapping
    ``bind_bar_for_mv2_wiring_v1`` and the warmup-observation bind path),
    looks up ``eligibility_mask_from_bars(bars)`` for that timestamp, and
    forces any mapped ``+1``/``-1`` (new entry intent) to ``0`` (stand
    aside) when the bar is ineligible. Mapped ``0`` (flat/exit) always
    passes through unchanged. Returns a mutable counters dict with
    ``entries_blocked_by_gate`` incremented once per bar where the gate
    actually changed the mapped signal.
    """
    counters = {"entries_blocked_by_gate": 0}
    if not enabled:
        yield counters
        return
    if bars is None:
        raise ValueError("ELIGIBILITY_GATE_BARS_REQUIRED")

    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    mask = eligibility_mask_from_bars(bars)
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
        eligible = bool(mask.asof(ts)) if ts is not None and len(mask) else False
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
    eligible_mask: pd.Series,
    entries_blocked_by_gate: int = 0,
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

    # RSI-exhaustion eligibility attribution on the decision segment.
    # NOTE: this is INFORMATIONAL ONLY — it reflects the (post-gate) resulting
    # trade entry times against the eligibility mask, not proof that the gate
    # blocked anything. For the baseline (ungated) arm a non-zero
    # `entries_on_ineligible_mask_bars` means the *unfiltered* strategy would
    # have entered on an ineligible bar; it is NOT the same as
    # `entries_blocked_by_gate`, which is the gate-effective, monkeypatch-based
    # counter of mapped +-1 -> 0 signal overrides (the primary divergence proof).
    mask_dec = eligible_mask.reindex(eq_dec.index).fillna(False)
    eligible_bar_share = float(mask_dec.mean()) if len(mask_dec) else 0.0
    entries_eligible = 0
    entries_on_ineligible_mask_bars = 0
    for r in filtered:
        et = _entry_ts(r)
        elig = bool(eligible_mask.asof(et)) if len(eligible_mask) else False
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
        native = member["native_instrument_id"]
        canon = member["canonical_instrument_id"]
        bars = load_member_bars(
            archive_root,
            native_instrument_id=native,
            start_inclusive=load_start,
            end_exclusive=decision_end,
        )
        eligible_mask = eligibility_mask_from_bars(bars)
        # Gate context is per-instrument (bound to this member's bars) because
        # run_arm loops members and the mask must match the bars currently
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
            eligible_mask=eligible_mask,
            entries_blocked_by_gate=counters["entries_blocked_by_gate"],
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
    assert_frozen_parameters_match_contract(contract)
    freeze = formula_freeze_payload()
    (output_dir / "eligibility_filter_formula_freeze.json").write_text(
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
    # Warmup: max feature lookback (eligibility filter) + bb period before decision start.
    bb_period = int(cfg["economic_evaluation_v1"]["strategy_params"]["bb_period"])
    max_feature_lookback_hours = int(contract["eligibility_filter"]["max_feature_lookback_hours"])
    load_start_ts = pd.Timestamp(decision_start) - pd.Timedelta(
        hours=max_feature_lookback_hours + bb_period
    )
    load_start = load_start_ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    # EXACTLY one evaluation: baseline (control, unfiltered) then treatment
    # (RSI-exhaustion eligibility gated) — two arms, one run.
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
    # mapped +-1 -> 0 signal overrides on the treatment arm. This is the
    # actual, engine-effective count of entries the gate suppressed — unlike
    # a bare `mask.asof(baseline entry_time)` count, it is only non-zero if
    # the gate genuinely altered MV2 replay behavior.
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

    # INFORMATIONAL ONLY (do NOT use as the primary divergence proof — a
    # non-zero value here on the baseline/ungated arm alone does not prove
    # the gate changed anything; see entries_blocked_by_gate above).
    baseline_entries_on_ineligible_mask_bars = sum(
        int(r["entries_on_ineligible_mask_bars"]) for r in baseline.rows
    )
    informational_divergent_members = [
        r["member_id"] for r in baseline.rows if int(r["entries_on_ineligible_mask_bars"]) > 0
    ]

    entry_eligibility_divergence_observed = (
        entries_blocked_by_gate > 0 or trade_count_differs or entry_times_differ
    )

    # Fail-closed: if the baseline showed ineligible-bar entries but the
    # gate-effective counter is zero and the arms are otherwise identical,
    # the gate is not actually reaching the engine's entry decision (the
    # original bug). Ship no economics in that state.
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

    config_snapshot = {
        "schema_version": "evaluate_rsi_exhaustion_mr_eligibility_development_config_snapshot.v1",
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
        "rsi_exhaustion_eligibility_filter_v1.py": _sha256_file(
            repo
            / "src/research/rsi_exhaustion_mr_eligibility_development_evaluation_v1"
            / "rsi_exhaustion_eligibility_filter_v1.py"
        ),
        "entry_eligibility_gate_v1.py": _sha256_file(
            repo
            / "src/research/rsi_exhaustion_mr_eligibility_development_evaluation_v1"
            / "entry_eligibility_gate_v1.py"
        ),
        "panel_runner_v1.py": _sha256_file(
            repo
            / "src/research/rsi_exhaustion_mr_eligibility_development_evaluation_v1"
            / "panel_runner_v1.py"
        ),
        "contract": canonical_json_sha256(contract),
        "feature_formula_sha256": freeze["feature_formula_sha256"],
    }
    (output_dir / "code_config_hashes.json").write_text(
        json.dumps(code_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    command = (
        "PYTHONPATH=src:. python3 scripts/research/"
        "run_evaluate_rsi_exhaustion_mr_eligibility_development_v1.py "
        f"--output-dir {output_dir}"
    )
    base_sha = _git_base_sha(repo)
    summary = {
        "schema_version": "evaluate_rsi_exhaustion_mr_eligibility_development_summary.v1",
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
        "decision_segment_note": (
            "Only the final_development_confirmation segment is evaluated per "
            "contract decision_thresholds.decision_segment; train_definition and "
            "validation segments are opaque split boundaries not used for this "
            "decision (walk-forward not applicable to a single locked "
            "decision-segment evaluation)."
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
        "base_sha": base_sha,
        "python_version": sys.version.split()[0],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    return summary


__all__ = ["run_development_evaluation", "EVALUATION_RUN_ID", "CONFIG_ID"]
