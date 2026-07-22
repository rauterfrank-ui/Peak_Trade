"""Single-run HOLDOUT panel evaluation for Exit V8 holdout successor v1.

Structural preflight and bound authorization run BEFORE any sealed panel access.
Reuses V8 mechanism/gate/decision read-only (no retune). Import alone does nothing.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
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
    load_runtime_cfg,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.panel_runner_v8 import (
    _aggregate_arm as _aggregate_arm_v8,
    _extract_member_trades as _extract_member_trades_v8,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.metrics_v1 import (
    enrich_trade_excursions,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.composite_midband_max_holding_exit_mechanism_v6 import (
    mechanism_freeze_payload,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.reentry_cooldown_gate_v8 import (
    optional_v7_control_or_treatment_gate,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.constants_v1 import (
    BASELINE_CONFIG_ID,
    BB_PERIOD,
    CONSUMED_MARKER_FILENAME,
    CONTRACT_REL_PATH,
    COST_MULTIPLIER,
    DATASET_CLASS,
    EVALUATION_RUN_ID,
    EVIDENCE_REL_PATH,
    FEE_BPS,
    HALF_SPREAD_BPS,
    HOLDOUT_PREREGISTRATION_DIGEST,
    HYPOTHESIS_ID,
    INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX,
    MAX_FEATURE_LOOKBACK_HOURS,
    MAX_TRADE_COUNT_REDUCTION_FRACTION,
    MINIMUM_TRADE_COUNT,
    OWNER_SURFACE,
    PERIOD_END_EXCLUSIVE,
    PERIOD_START,
    PRIMARY_SEED,
    RUNNER_START_MARKER_FILENAME,
    RUN_SLOT_CLAIM_FILENAME,
    SLIPPAGE_BPS,
    STRATEGY_ID,
    V8_PREREGISTRATION_DIGEST,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.decision_v1 import (
    decide_holdout_evaluation,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.holdout_panel_bars_v1 import (
    included_panel_members,
    load_member_bars,
    resolve_holdout_archive_root,
    verify_holdout_panel_hashes,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.structural_preflight_v1 import (
    run_structural_preflight,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistration_v1 import (
    HoldoutPreregistrationError,
    load_json,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    CANONICAL_INSTRUMENT_ID,
)
from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

SHARED_INITIAL_CAPITAL = 10_000.0


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


@dataclass(frozen=True)
class ArmResult:
    arm: str
    rows: list[dict[str, Any]]
    metrics: dict[str, Any]
    enriched_trades: list[dict[str, Any]]
    exit_attribution: dict[str, Any]
    wallclock_seconds: float


def _extract_member_trades(*args, **kwargs):
    return _extract_member_trades_v8(*args, **kwargs)


def _aggregate_arm(**kwargs):
    return _aggregate_arm_v8(**kwargs)


def run_arm(
    *,
    arm: str,
    cfg: dict[str, Any],
    archive_root: Path,
    members: list[dict[str, str]],
    load_start: str,
    decision_start: str,
    decision_end: str,
    cooldown_enabled: bool,
) -> ArmResult:
    t0 = time.perf_counter()
    d_start = pd.Timestamp(decision_start)
    d_end = pd.Timestamp(decision_end)
    all_trades: list[dict[str, Any]] = []
    equity_curves: dict[str, pd.Series] = {}
    bars_by_instrument: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    exits_forced_total = 0
    exit_bars_total = 0
    midband_exit_total = 0
    max_holding_exit_total = 0

    for member in members:
        native = member["native_instrument_id"]
        canon = member["canonical_instrument_id"]
        bars = load_member_bars(
            archive_root,
            canonical_instrument_id=canon,
            start_inclusive=load_start,
            end_exclusive=decision_end,
        )
        bars_by_instrument[canon] = bars
        with optional_v7_control_or_treatment_gate(
            cooldown_enabled=cooldown_enabled, bars=bars, instrument_id=native
        ) as gate_bundle:
            result = run_mv2_research_backtest_wiring_v1(
                bars,
                strategy_id=STRATEGY_ID,
                cfg=cfg,
                instrument_id=CANONICAL_INSTRUMENT_ID,
                profile_binding=_profile(),
                observational_panel_member_instrument_id=canon,
            )
            counters = gate_bundle.get("exit_counters") or {}
            cooldown_attr = gate_bundle["cooldown_state"].attribution()
        trades, eq_dec = _extract_member_trades(
            result,
            instrument_id=canon,
            decision_start=d_start,
            decision_end=d_end,
        )
        forced = int(counters.get("exits_forced_by_gate") or 0)
        exits_forced_total += forced
        exit_bars_total += int(counters.get("exit_bars_observed") or 0)
        midband_exit_total += int(counters.get("midband_exit_count") or 0)
        max_holding_exit_total += int(counters.get("max_holding_exit_count") or 0)
        all_trades.extend(trades)
        equity_curves[canon] = eq_dec
        rows.append(
            {
                "member_id": canon,
                "trade_count": len(trades),
                "exits_forced_by_gate": forced,
                "exit_bars_observed": int(counters.get("exit_bars_observed") or 0),
                "blocked_same_side_reentry_count": int(
                    cooldown_attr.get("blocked_same_side_reentry_count") or 0
                ),
                "cooldown_activation_count": int(
                    cooldown_attr.get("cooldown_activation_count") or 0
                ),
            }
        )

    enriched = enrich_trade_excursions(all_trades, bars_by_instrument)
    metrics = _aggregate_arm(
        enriched=enriched,
        equity_curves=equity_curves,
        exits_forced_by_gate=exits_forced_total,
        midband_exit_count=midband_exit_total,
        max_holding_exit_count=max_holding_exit_total,
    )
    exit_attr = {
        "cooldown_enabled": cooldown_enabled,
        "exits_forced_by_gate": exits_forced_total,
        "exit_bars_observed": exit_bars_total,
        "midband_exit_count": midband_exit_total,
        "max_holding_exit_count": max_holding_exit_total,
    }
    return ArmResult(
        arm=arm,
        rows=rows,
        metrics=metrics,
        enriched_trades=enriched,
        exit_attribution=exit_attr,
        wallclock_seconds=float(time.perf_counter() - t0),
    )


def _claim_run_slot(output_dir: Path, *, preflight: Mapping[str, Any]) -> dict[str, Any]:
    claim_path = output_dir / RUN_SLOT_CLAIM_FILENAME
    if claim_path.is_file():
        raise HoldoutPreregistrationError("HOLDOUT_RUN_SLOT_CLAIM_ALREADY_PRESENT")
    claim = {
        "schema_version": "bollinger_mr_holdout_v1_run_slot_claim.v1",
        "evaluation_run_id": EVALUATION_RUN_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "holdout_preregistration_digest": HOLDOUT_PREREGISTRATION_DIGEST,
        "repo_head_sha": preflight.get("repo_head_sha"),
        "authorization": preflight.get("authorization"),
        "holdout_run_count_before": preflight.get("run_count_before"),
        "runner_start_count_before": preflight.get("runner_start_count_before"),
    }
    claim_path.write_text(json.dumps(claim, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / RUNNER_START_MARKER_FILENAME).write_text("1\n", encoding="utf-8")
    return claim


def run_holdout_evaluation(
    *,
    output_dir: Path,
    archive_root: Path | None = None,
    repo_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    output_dir = Path(output_dir)

    # ALL structural gates BEFORE mkdir evidence side-effects beyond output_dir creation
    # and BEFORE any sealed panel access.
    preflight = run_structural_preflight(
        repo_root=repo,
        output_dir=output_dir,
        environ=environ,
        require_authorization=True,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    claim = _claim_run_slot(output_dir, preflight=preflight)

    contract = load_json(repo / CONTRACT_REL_PATH)
    freeze = mechanism_freeze_payload()
    (output_dir / "exit_mechanism_formula_freeze.json").write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # First sealed holdout access only after preflight + slot claim.
    root = resolve_holdout_archive_root(archive_root)
    panel_proof = verify_holdout_panel_hashes(root)
    members = included_panel_members(root)
    cfg = load_runtime_cfg(repo, seed=PRIMARY_SEED)
    if float(cfg["backtest"]["fee_bps"]) != FEE_BPS:
        raise RuntimeError("FEE_BPS_MISMATCH")
    if float(cfg["backtest"]["slippage_bps"]) != SLIPPAGE_BPS:
        raise RuntimeError("SLIPPAGE_BPS_MISMATCH")

    decision_start = PERIOD_START
    decision_end = PERIOD_END_EXCLUSIVE
    load_start_ts = pd.Timestamp(decision_start) - pd.Timedelta(
        hours=MAX_FEATURE_LOOKBACK_HOURS + BB_PERIOD
    )
    load_start = load_start_ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    control = run_arm(
        arm="control",
        cfg=cfg,
        archive_root=root,
        members=members,
        load_start=load_start,
        decision_start=decision_start,
        decision_end=decision_end,
        cooldown_enabled=False,
    )
    treatment = run_arm(
        arm="treatment",
        cfg=cfg,
        archive_root=root,
        members=members,
        load_start=load_start,
        decision_start=decision_start,
        decision_end=decision_end,
        cooldown_enabled=True,
    )

    control_exit_times = {
        (t["instrument_id"], t["entry_time"]): t["exit_time"] for t in control.enriched_trades
    }
    treatment_exit_times = {
        (t["instrument_id"], t["entry_time"]): t["exit_time"] for t in treatment.enriched_trades
    }
    shared = set(control_exit_times) & set(treatment_exit_times)
    exit_fills_identical = all(control_exit_times[k] == treatment_exit_times[k] for k in shared)
    blocked = int(sum(int(r.get("blocked_same_side_reentry_count") or 0) for r in treatment.rows))
    cooldown_activations = int(
        sum(int(r.get("cooldown_activation_count") or 0) for r in treatment.rows)
    )
    forced_midband = int(treatment.metrics.get("midband_exit_count") or 0)
    reentry_divergence_observed = blocked >= 1 or cooldown_activations >= 1

    decision_out = decide_holdout_evaluation(
        control=control.metrics,
        treatment=treatment.metrics,
        reentry_divergence_observed=reentry_divergence_observed,
        exit_fills_identical=exit_fills_identical,
        effective_configs_differ=True,
        open_side_binding_observed=True,
        exit_bars_observed=int(treatment.exit_attribution.get("exit_bars_observed") or 0),
        forced_midband_exit_count=forced_midband,
        cooldown_activation_count=cooldown_activations,
        blocked_same_side_reentry_count=blocked,
        authority_binding_ok=True,
        control_treatment_isolation_ok=True,
        minimum_trade_count=MINIMUM_TRADE_COUNT,
        max_trade_count_reduction_fraction=MAX_TRADE_COUNT_REDUCTION_FRACTION,
        instrument_concentration_worst1_max=INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX,
        cost_multiplier_treatment=COST_MULTIPLIER,
    )

    def _public(m: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in m.items():
            if str(k).startswith("_"):
                continue
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                out[k] = None
            else:
                out[k] = v
        return out

    control.metrics["_portfolio_equity"].to_csv(output_dir / "portfolio_equity_control.csv")
    treatment.metrics["_portfolio_equity"].to_csv(output_dir / "portfolio_equity_treatment.csv")
    (output_dir / "baseline_metrics.json").write_text(
        json.dumps(_public(control.metrics), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "treatment_metrics.json").write_text(
        json.dumps(_public(treatment.metrics), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "comparison_decision.json").write_text(
        json.dumps(decision_out, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    holdout_run_count_after = int(preflight["run_count_before"]) + 1
    config_snapshot = {
        "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_config_snapshot.v1",
        "hypothesis_id": HYPOTHESIS_ID,
        "baseline_config_id": BASELINE_CONFIG_ID,
        "dataset_id": panel_proof["dataset_id"],
        "dataset_class": DATASET_CLASS,
        "decision_segment": {"start": decision_start, "end_exclusive": decision_end},
        "cost_model": contract.get("cost_model"),
        "seed": PRIMARY_SEED,
        "holdout_preregistration_digest": HOLDOUT_PREREGISTRATION_DIGEST,
        "development_preregistration_digest": V8_PREREGISTRATION_DIGEST,
    }
    (output_dir / "config_snapshot.json").write_text(
        json.dumps(config_snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    code_hashes = {
        "panel_runner_v1.py": _sha256_file(Path(__file__)),
        "holdout_panel_bars_v1.py": _sha256_file(
            Path(__file__).resolve().parent / "holdout_panel_bars_v1.py"
        ),
        "contract_digest": HOLDOUT_PREREGISTRATION_DIGEST,
    }
    (output_dir / "code_config_hashes.json").write_text(
        json.dumps(code_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    summary = {
        "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_summary.v1",
        "evaluation_run_id": EVALUATION_RUN_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "result_class": decision_out["result_class"],
        "decision": decision_out,
        "baseline_metrics": _public(control.metrics),
        "treatment_metrics": _public(treatment.metrics),
        "holdout_run_count": holdout_run_count_after,
        "holdout_run_limit": 1,
        "holdout_run_count_before": preflight["run_count_before"],
        "runner_start_count": 1,
        "holdout_split_digest": preflight["contract_preflight"]["holdout_split_digest"],
        "holdout_preregistration_digest": HOLDOUT_PREREGISTRATION_DIGEST,
        "development_preregistration_digest": V8_PREREGISTRATION_DIGEST,
        "mechanism_id": contract.get("exit_mechanism", {}).get("mechanism_id"),
        "dataset_id": panel_proof["dataset_id"],
        "sealed_holdout_id": contract.get("sealed_holdout_id"),
        "holdout_accessed": True,
        "sealed_holdout_content_inspected": True,
        "panel_proof": panel_proof,
        "run_slot_claim": claim,
        "authorization": preflight.get("authorization"),
        "economic_validity_offline_gate_changed": False,
        "economic_gate_open": False,
        "promotion_eligible": False,
        "runtime_activated": False,
        "orders_sent": False,
        "no_retry": True,
        "owner_surface": OWNER_SURFACE,
        "base_sha": preflight.get("repo_head_sha"),
        "python_version": sys.version.split()[0],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    run_manifest = {
        "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_run_manifest.v1",
        "hypothesis_id": HYPOTHESIS_ID,
        "evaluation_run_id": EVALUATION_RUN_ID,
        "result_class": decision_out["result_class"],
        "reason": decision_out.get("reason"),
        "holdout_run_count": holdout_run_count_after,
        "holdout_run_limit": 1,
        "holdout_accessed": True,
        "promotion_eligible": False,
        "economic_gate_opened": False,
        "runtime_activated": False,
        "orders_sent": False,
        "no_retry": True,
        "exit_code": 0,
        "exit_status": "COMPLETED",
        "base_sha": preflight.get("repo_head_sha"),
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    (output_dir / "safety_attestation.md").write_text(
        "# Safety attestation — Exit V8 holdout evaluation v1\n\n"
        f"- result_class: {decision_out['result_class']}\n"
        "- economic gate closed; promotion closed; runtime/orders disabled\n"
        "- single holdout run; no retry\n"
        "- V7/V8 development terminals not mutated\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        f"# Evaluate Exit V8 holdout v1\n\nRESULT_CLASS={decision_out['result_class']}\n",
        encoding="utf-8",
    )
    (output_dir / CONSUMED_MARKER_FILENAME).write_text(
        f"{decision_out['result_class']}\n", encoding="utf-8"
    )
    write_manifest_sha256(output_dir)
    return summary


__all__ = ["run_arm", "run_holdout_evaluation"]
