"""Orchestrate read-only Bollinger/MR economic failure decomposition on DEVELOPMENT_ONLY panel."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.backtest.admissible_versioned_futures_dataset_v1 import (
    DatasetProfileBindingV1,
    DatasetProfileV1,
    ExecutionCostBindingV1,
    L1ObservationStatusV1,
)
from src.backtest.mv2_research_wiring_v1 import run_mv2_research_backtest_wiring_v1
from src.research.adx_di_direction_confirmation_mr_eligibility_development_evaluation_v1.panel_runner_v1 import (
    _classify_side,
    load_runtime_cfg,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.binding_v1 import (
    DecompositionBindingError,
    assert_baseline_binding_digests,
    assert_contract_gates,
    assert_panel_index_and_state_binding,
    assert_parent_baseline_ledger_binding,
    load_contract,
    reject_holdout_access,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.classify_v1 import (
    classify_economic_failure,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.constants_v1 import (
    BASELINE_CONFIG_ID,
    DATASET_CLASS,
    DATASET_ID,
    DECISION_END_EXCLUSIVE,
    DECISION_START,
    DEVELOPMENT_SPLIT_DIGEST,
    EVIDENCE_CLASS_ID,
    EVIDENCE_REL_PATH,
    EXECUTION_ID,
    FEE_BPS,
    HALF_SPREAD_BPS,
    MAX_FEATURE_LOOKBACK_HOURS,
    PARENT_BASELINE_EVIDENCE_REF,
    PARENT_BASELINE_METRICS,
    PORTFOLIO_AGGREGATION_ID,
    PRIMARY_SEED,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    SHARED_INITIAL_CAPITAL,
    SLIPPAGE_BPS,
    SLEEVE_INITIAL_CASH,
    STRATEGY_ID,
    STRATEGY_VERSION,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.metrics_v1 import (
    aggregate_core_metrics,
    concentration_stats,
    cost_stress_table,
    enrich_trade_excursions,
    instrument_attribution,
    side_attribution,
)
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (
    included_panel_members,
    load_member_bars,
    resolve_development_archive_root,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.shared_portfolio_equity_research_v1 import (
    build_equal_weight_portfolio_equity,
    portfolio_metrics_from_equity,
)
from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_sha(repo: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(repo), text=True, timeout=10
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


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


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _extract_trades_for_member(
    *,
    result: Any,
    instrument_id: str,
    decision_start: pd.Timestamp,
    decision_end: pd.Timestamp,
) -> tuple[list[dict[str, Any]], pd.Series]:
    bt = result.backtest_result
    trades_df = getattr(bt, "trades", None)
    trade_records: list[dict[str, Any]] = []
    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trade_records = trades_df.to_dict(orient="records")

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
        if not (decision_start <= ets < decision_end):
            continue
        side = _classify_side(rec)
        if side not in {"long", "short"}:
            raise DecompositionBindingError(f"TRADE_SIDE_UNKNOWN:{side}")
        fees = rec.get("fee_total")
        if fees is None:
            fees = rec.get("fee")
        if fees is None:
            raise DecompositionBindingError("TRADE_FEES_MISSING")
        slip = rec.get("slippage_total")
        if slip is None:
            raise DecompositionBindingError("TRADE_SLIPPAGE_MISSING")
        gross = rec.get("gross_pnl")
        net = rec.get("pnl")
        if gross is None or net is None:
            raise DecompositionBindingError("TRADE_PNL_MISSING")
        if rec.get("entry_price") is None:
            raise DecompositionBindingError("ENTRY_PRICE_MISSING")
        filtered.append(
            {
                "instrument_id": instrument_id,
                "side": side,
                "entry_time": str(rec.get("entry_time")),
                "exit_time": str(rec.get("exit_time")),
                "entry_price": float(rec["entry_price"]),
                "exit_price": float(rec["exit_price"])
                if rec.get("exit_price") is not None
                else None,
                "size": float(rec["size"]) if rec.get("size") is not None else None,
                "gross_pnl": float(gross),
                "fees": float(fees),
                "slippage": float(slip),
                "net_pnl": float(net),
                "exit_reason": str(rec.get("exit_reason") or "UNKNOWN"),
            }
        )

    equity = getattr(bt, "equity_curve", None)
    if equity is None or len(equity) == 0:
        raise DecompositionBindingError(f"MISSING_EQUITY:{instrument_id}")
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
    return filtered, eq_dec


def run_baseline_decomposition(
    *,
    output_dir: Path | None = None,
    archive_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Replay immutable Bollinger baseline on DEVELOPMENT_ONLY panel and decompose failure."""
    repo = repo_root or _repo_root()
    out = output_dir or (repo / EVIDENCE_REL_PATH)
    out.mkdir(parents=True, exist_ok=True)

    config = load_contract(repo)
    assert_contract_gates(config)
    baseline_digests = assert_baseline_binding_digests(repo, config)

    reject_holdout_access(DATASET_ID)

    root = resolve_development_archive_root(archive_root)
    panel_proof = assert_panel_index_and_state_binding(root)
    members = included_panel_members(root)
    if not members:
        raise DecompositionBindingError("PANEL_MEMBERS_EMPTY")

    cfg = load_runtime_cfg(repo, seed=PRIMARY_SEED)
    # Fail closed: frozen costs must match contract.
    if float(cfg["backtest"]["fee_bps"]) != FEE_BPS:
        raise DecompositionBindingError("FEE_BPS_MISMATCH")
    if float(cfg["backtest"]["slippage_bps"]) != SLIPPAGE_BPS:
        raise DecompositionBindingError("SLIPPAGE_BPS_MISMATCH")

    decision_start = pd.Timestamp(DECISION_START)
    decision_end = pd.Timestamp(DECISION_END_EXCLUSIVE)
    bb_period = int(cfg["economic_evaluation_v1"]["strategy_params"]["bb_period"])
    load_start_ts = decision_start - pd.Timedelta(hours=MAX_FEATURE_LOOKBACK_HOURS + bb_period)
    load_start = load_start_ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    t0 = time.perf_counter()
    all_trades: list[dict[str, Any]] = []
    equity_curves: dict[str, pd.Series] = {}
    bars_by_instrument: dict[str, pd.DataFrame] = {}

    for i, member in enumerate(members, start=1):
        native = member["native_instrument_id"]
        canon = member["canonical_instrument_id"]
        bars = load_member_bars(
            root,
            native_instrument_id=native,
            start_inclusive=load_start,
            end_exclusive=DECISION_END_EXCLUSIVE,
        )
        bars_by_instrument[canon] = bars
        result = run_mv2_research_backtest_wiring_v1(
            bars,
            strategy_id=STRATEGY_ID,
            cfg=cfg,
            instrument_id=CANONICAL_INSTRUMENT_ID,
            profile_binding=_profile(),
            observational_panel_member_instrument_id=canon,
        )
        trades, eq_dec = _extract_trades_for_member(
            result=result,
            instrument_id=canon,
            decision_start=decision_start,
            decision_end=decision_end,
        )
        all_trades.extend(trades)
        equity_curves[canon] = eq_dec
        print(
            json.dumps(
                {
                    "phase": "baseline_decomposition",
                    "i": i,
                    "n": len(members),
                    "member": native,
                    "trades": len(trades),
                }
            ),
            flush=True,
        )

    wallclock = float(time.perf_counter() - t0)
    enriched = enrich_trade_excursions(all_trades, bars_by_instrument)
    core = aggregate_core_metrics(enriched)
    side = side_attribution(enriched)
    instruments = instrument_attribution(enriched)
    concentration = concentration_stats(instruments)
    cost_stress = cost_stress_table(enriched)

    # Sleeve-sum ledger binding to parent sealed baseline (same control arm).
    assert_parent_baseline_ledger_binding(
        observed={
            "trade_count": core["trade_count"],
            "long_trades": side["long"]["trade_count"],
            "short_trades": side["short"]["trade_count"],
            "gross_pnl": core["gross_pnl"],
            "fees": core["fees"],
            "slippage": core["slippage"],
            "net_pnl": core["net_pnl"],
        }
    )

    portfolio_eq = build_equal_weight_portfolio_equity(
        equity_curves, initial_capital=SHARED_INITIAL_CAPITAL
    )
    port = portfolio_metrics_from_equity(portfolio_eq, initial_capital=SHARED_INITIAL_CAPITAL)

    classification = classify_economic_failure(
        core=core,
        side=side,
        cost_stress=cost_stress,
        concentration=concentration,
    )

    next_question = str(
        config.get("next_research_question")
        or (
            "Given ENTRY_HAS_NO_GROSS_EDGE on the sealed DEVELOPMENT_ONLY Bollinger/MR baseline, "
            "does a non-eligibility structural change class (distinct from exhausted entry-filter "
            "families) exist that can create gross edge without retuning terminal parameters?"
        )
    )

    summary = {
        "artifact_kind": "bollinger_mr_economic_failure_decomposition_development_summary",
        "artifact_version": "v1",
        "scope_id": SCOPE_ID,
        "execution_id": EXECUTION_ID,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "process_classification": PROCESS_CLASSIFICATION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
        "non_authorizing": True,
        "diagnostic_only": True,
        "new_hypothesis_tested": False,
        "holdout_data_accessed": False,
        "holdout_rerun_executed": False,
        "economic_validity_offline_gate_pass": False,
        "promotion_eligible": False,
        "runtime_activated": False,
        "orders_sent": False,
        "production_strategy_semantics_changed": False,
        "double_play_authority_changed": False,
        "risk_sizing_execution_semantics_changed": False,
        "dataset_id": DATASET_ID,
        "dataset_class": DATASET_CLASS,
        "baseline_config_id": BASELINE_CONFIG_ID,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "portfolio_aggregation_id": PORTFOLIO_AGGREGATION_ID,
        "development_period": f"{DECISION_START}..{DECISION_END_EXCLUSIVE}",
        "development_split_digest": DEVELOPMENT_SPLIT_DIGEST,
        "seed": PRIMARY_SEED,
        "cost_model": {
            "fee_bps": FEE_BPS,
            "slippage_bps": SLIPPAGE_BPS,
            "half_spread_bps": HALF_SPREAD_BPS,
            "fixed": True,
        },
        "baseline_binding_digests": baseline_digests,
        "panel_proof": panel_proof,
        "parent_baseline_evidence_ref": PARENT_BASELINE_EVIDENCE_REF,
        "parent_baseline_metrics": PARENT_BASELINE_METRICS,
        "core_metrics": core,
        "side_attribution": side,
        "instrument_attribution": instruments,
        "concentration": concentration,
        "cost_stress": cost_stress,
        "classification": classification,
        "diagnostic_class": classification["diagnostic_class"],
        "flags": classification["flags"],
        "portfolio_metrics": {
            "net_return": float(port["net_return"]),
            "sharpe": float(port["sharpe"]),
            "max_drawdown": float(port["max_drawdown"]),
            "final_equity": float(port["final_equity"]),
        },
        "wallclock_seconds": wallclock,
        "instrument_count": len(members),
        "base_sha": _git_sha(repo),
        "timestamp_utc": _utc_now(),
        "next_research_question": next_question,
        "action_recommendation": None,
        "new_hypothesis": None,
    }

    trade_ledger = {
        "schema_version": "bollinger_mr_economic_failure_decomposition_trade_ledger.v1",
        "dataset_id": DATASET_ID,
        "baseline_config_id": BASELINE_CONFIG_ID,
        "trade_count": len(enriched),
        "trades": enriched,
    }

    code_hashes = {
        "decompose_v1.py": _sha256_file(Path(__file__)),
        "classify_v1.py": _sha256_file(Path(__file__).with_name("classify_v1.py")),
        "metrics_v1.py": _sha256_file(Path(__file__).with_name("metrics_v1.py")),
        "binding_v1.py": _sha256_file(Path(__file__).with_name("binding_v1.py")),
        "constants_v1.py": _sha256_file(Path(__file__).with_name("constants_v1.py")),
        "contract": _sha256_file(
            repo / "config/research/bollinger_mr_economic_failure_decomposition_development_v1.json"
        ),
    }

    safety = "\n".join(
        [
            "# Safety attestation",
            "",
            "HOLDOUT_DATA_ACCESSED=false",
            "HOLDOUT_RERUN_EXECUTED=false",
            "ECONOMIC_GATE_OPEN=false",
            "PROMOTION_GATE_OPEN=false",
            "RUNTIME_ACTIVATED=false",
            "ORDERS_SENT=false",
            "PRODUCTION_STRATEGY_SEMANTICS_CHANGED=false",
            "DOUBLE_PLAY_AUTHORITY_CHANGED=false",
            "RISK_SIZING_EXECUTION_SEMANTICS_CHANGED=false",
            "NEW_HYPOTHESIS_TESTED=false",
            "PARAMETER_TUNING=false",
            "",
        ]
    )

    _write_json(out / "summary.json", summary)
    _write_json(out / "FAILURE_DECOMPOSITION.json", summary)
    _write_json(out / "core_metrics.json", core)
    _write_json(out / "side_attribution.json", side)
    _write_json(out / "instrument_attribution.json", {"instruments": instruments, **concentration})
    _write_json(out / "cost_stress.json", {"rows": cost_stress})
    _write_json(out / "classification.json", classification)
    _write_json(out / "trade_ledger.json", trade_ledger)
    _write_json(out / "code_config_hashes.json", code_hashes)
    _write_json(
        out / "config_snapshot.json",
        {
            "scope_id": SCOPE_ID,
            "dataset_id": DATASET_ID,
            "baseline_config_id": BASELINE_CONFIG_ID,
            "decision_segment": {
                "start": DECISION_START,
                "end_exclusive": DECISION_END_EXCLUSIVE,
            },
            "development_split_digest": DEVELOPMENT_SPLIT_DIGEST,
            "seed": PRIMARY_SEED,
            "cost_model": summary["cost_model"],
            "baseline_binding_digests": baseline_digests,
        },
    )
    _write_json(
        out / "run_manifest.json",
        {
            "execution_id": EXECUTION_ID,
            "evidence_class_id": EVIDENCE_CLASS_ID,
            "wallclock_seconds": wallclock,
            "base_sha": summary["base_sha"],
            "timestamp_utc": summary["timestamp_utc"],
            "archive_root": str(root),
            "output_dir": str(out),
        },
    )
    (out / "safety_attestation.md").write_text(safety, encoding="utf-8")
    (out / "determinism_repro.txt").write_text(
        "\n".join(
            [
                f"SCOPE_ID={SCOPE_ID}",
                f"DATASET_ID={DATASET_ID}",
                f"BASELINE_CONFIG_ID={BASELINE_CONFIG_ID}",
                f"SEED={PRIMARY_SEED}",
                f"DEVELOPMENT_SPLIT_DIGEST={DEVELOPMENT_SPLIT_DIGEST}",
                f"PARENT_BASELINE_TRADE_COUNT={PARENT_BASELINE_METRICS['trade_count']}",
                "COMMAND=PYTHONPATH=src:. python3 scripts/research/"
                "run_bollinger_mr_economic_failure_decomposition_development_v1.py",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "README.md").write_text(
        "\n".join(
            [
                "# Bollinger/MR Economic Failure Decomposition (DEVELOPMENT_ONLY) v1",
                "",
                "Read-only diagnostic decomposition of the immutable Bollinger/MR baseline",
                "on the sealed DEVELOPMENT_ONLY panel. Non-authorizing. No holdout access.",
                "No new hypothesis. No economic/promotion gate open.",
                "",
                f"DIAGNOSTIC_CLASS={classification['diagnostic_class']}",
                f"DATASET_ID={DATASET_ID}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_manifest_sha256(out)
    return summary
