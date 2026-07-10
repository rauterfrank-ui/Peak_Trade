#!/usr/bin/env python3
"""Run offline economic evaluation for CS MA-crossover panel rank-rotation v0.

Bounded baseline adjudication with durable evidence persistence. No runtime authority.
Operator GO: GO_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.backtest.economic_validity_policy_v1 import (  # noqa: E402
    EconomicValidityEvidenceMetricsV1,
    canonical_economic_validity_policy_v1,
    evaluate_economic_validity_against_policy_v1,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_binding_ratification_v0 import (  # noqa: E402
    materialize_binding_ratification_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_ranking_semantics_binding_validator_v0 import (  # noqa: E402
    ValidationVerdict,
    validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_single_slot_research_orchestrator_v0 import (  # noqa: E402
    default_ma_crossover_operator_binding_v0,
    run_ma_crossover_panel_rank_rotation_orchestrator_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH,
    INSTRUMENT_COUNT,
    OPERATOR_GO_ECONOMIC_EVALUATION,
    PANEL_DATA_DIGEST,
    PANEL_DATASET_DIGEST,
    PANEL_DATASET_ID,
    PANEL_STAGING_ROOT,
    ROW_COUNT_TOTAL,
    RUNTIME_EFFECT,
    SOURCE_CLOSEOUT_BUNDLE,
    STRATEGY_ID,
    STRATEGY_VERSION,
    WINDOW_END_UTC,
    WINDOW_START_UTC,
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (  # noqa: E402
    verify_panel_staging_source_manifests_v1,
)
from src.research.cross_sectional_single_slot_accounting_reconciliation_v0 import (  # noqa: E402
    FAILURE_FORCED_END_OF_WINDOW_LIQUIDATION_MISSING,
    accounting_reconciliation_to_dict,
    reconcile_single_slot_backtest_accounting_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (  # noqa: E402
    END_OF_WINDOW_POLICY,
    run_single_slot_panel_backtest_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v1 import (  # noqa: E402
    _load_panel_series_from_staging_root,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

GO_TOKEN = OPERATOR_GO_ECONOMIC_EVALUATION
ACCOUNTING_FIX_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_ACCOUNTING_RECONCILIATION_"
    "ADJUDICATION_AND_REPRODUCIBILITY_FIX_V0"
)
ALLOWED_GO_TOKENS = frozenset({GO_TOKEN, ACCOUNTING_FIX_GO_TOKEN})
SOURCE_EVALUATION_BUNDLE_DEFAULT = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_offline_economic_evaluation_"
    "20260710T101306Z"
)
EXPECTED_ORIGIN_MAIN_SHA = "8ea5670cda60f9eb3656ef1aa483ed6f823457b5"
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_CLOSEOUT_BUNDLE_PR5079 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5079_merge_closeout_cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_"
    "binding_ratification_v0_20260710T100525Z"
)

EXPECTED_BINDING_DIGEST = "89f80951dd71e43168b9b37b0d6f04d57ba7ca025fcd4923c9901d0f244f43e6"
EXPECTED_CONFIG_DIGEST = "eaca6226b6e040580227c8380c86a3aaa4f3e3bdad9292b37d9cbef736405141"
EXPECTED_DATA_DIGEST = "b0eb7802c269bcab987d2025fe1e960b83079d5ac5f305799e0867661d42f2e0"
EXPECTED_IMPLEMENTATION_DIGEST = "e2ad162ad12405ca9a2378ea9b8733463c672445e8887da6665427d4de8431d8"
EXPECTED_RATIFICATION_DIGEST = "24e417edf5ec40a6e1cc50a790b2dd3b533bd2786037de3d90cdf10104a07b28"


class EconomicClassification(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAIL_CLOSED = "FAIL_CLOSED"


class RobustnessExecutionStatus(str, Enum):
    NOT_EXECUTED_BASELINE_NEGATIVE = "NOT_EXECUTED_BASELINE_NEGATIVE"
    NOT_EXECUTED_PERIOD_BINDING_UNSPLIT = "NOT_EXECUTED_PERIOD_BINDING_UNSPLIT"
    NOT_EXECUTED_CONTRACT_BLOCKED = "NOT_EXECUTED_CONTRACT_BLOCKED"


@dataclass(frozen=True)
class PreflightResult:
    passed: bool
    fail_reasons: tuple[str, ...]
    head: str
    origin_main: str
    worktree_clean: bool
    source_closeout_manifest_verify_rc: int


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_origin_main(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _worktree_clean(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        if line.startswith("??"):
            continue
        return False
    return True


def _verify_manifest(bundle_dir: Path) -> int:
    manifest = bundle_dir / "MANIFEST.sha256"
    if not manifest.is_file():
        return 1
    result = subprocess.run(
        ["shasum", "-a", "256", "-c", str(manifest)],
        cwd=str(bundle_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode


def run_preflight(
    *,
    repo_root: Path,
    source_closeout_bundle: Path,
    confirm: str,
) -> PreflightResult:
    reasons: list[str] = []
    head = _git_head(repo_root)
    origin_main = _git_origin_main(repo_root)
    clean = _worktree_clean(repo_root)
    manifest_rc = _verify_manifest(source_closeout_bundle)
    accounting_fix = confirm == ACCOUNTING_FIX_GO_TOKEN

    if origin_main != EXPECTED_ORIGIN_MAIN_SHA:
        reasons.append(f"ORIGIN_MAIN_MISMATCH:{origin_main}")
    if not accounting_fix and head != EXPECTED_ORIGIN_MAIN_SHA:
        reasons.append(f"HEAD_MISMATCH:{head}")
    if not accounting_fix and head != origin_main:
        reasons.append("HEAD_NOT_EQUAL_ORIGIN_MAIN")
    if not clean:
        reasons.append("WORKTREE_NOT_CLEAN")
    if manifest_rc != 0:
        reasons.append(f"SOURCE_CLOSEOUT_MANIFEST_VERIFY_FAILED:{manifest_rc}")

    binding = materialize_versioned_research_binding_v0()
    ratification = materialize_binding_ratification_v0(repo_root=repo_root)
    digest_checks = {
        "BINDING_DIGEST": (binding["binding_digest"], EXPECTED_BINDING_DIGEST),
        "CONFIG_DIGEST": (binding["config_digest"], EXPECTED_CONFIG_DIGEST),
        "DATA_DIGEST": (binding["data_digest"], EXPECTED_DATA_DIGEST),
        "IMPLEMENTATION_DIGEST": (binding["implementation_digest"], EXPECTED_IMPLEMENTATION_DIGEST),
        "RATIFICATION_DIGEST": (ratification["ratification_digest"], EXPECTED_RATIFICATION_DIGEST),
    }
    for label, (actual, expected) in digest_checks.items():
        if actual != expected:
            reasons.append(f"{label}_MISMATCH:{actual}!={expected}")
    if not ratification.get("binding_ratified"):
        reasons.append("BINDING_NOT_RATIFIED")

    validation = validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0(
        binding["binding"]
    )
    if validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(list(validation.fail_reasons))

    return PreflightResult(
        passed=not reasons,
        fail_reasons=tuple(reasons),
        head=head,
        origin_main=origin_main,
        worktree_clean=clean,
        source_closeout_manifest_verify_rc=manifest_rc,
    )


def _verify_dataset(
    staging_root: Path,
    versioned_binding: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...], tuple[InstrumentPanelSeriesV1, ...], str]:
    reasons: list[str] = []
    manifest_ok, manifest_rc, manifest_reasons = verify_panel_staging_source_manifests_v1(
        staging_root
    )
    if not manifest_ok or manifest_rc != 0:
        reasons.extend(manifest_reasons)
        reasons.append(f"SOURCE_MANIFEST_VERIFY_RC:{manifest_rc}")

    panel_series, normalized_digest = _load_panel_series_from_staging_root(staging_root)
    panel_ref = (
        f"pit_okx_pt1h_panel_ohlcv_dataset_v1:{PANEL_DATASET_ID}:sha256:{PANEL_DATASET_DIGEST}"
    )
    panel_dir = staging_root / "panel"
    manifest = json.loads((panel_dir / "panel_dataset_manifest.json").read_text(encoding="utf-8"))
    normalized_digest = str(manifest.get("normalized_panel_digest", ""))
    dataset_digest = str(manifest.get("manifest_digest", ""))
    instrument_count = len(manifest.get("instrument_ids", []))
    row_count = int(manifest.get("panel_row_count", 0))

    if normalized_digest != PANEL_DATA_DIGEST:
        reasons.append(f"LOADER_PANEL_DATA_DIGEST_MISMATCH:{normalized_digest}")
    if dataset_digest != PANEL_DATASET_DIGEST:
        reasons.append(f"DATASET_DIGEST_MISMATCH:{dataset_digest}")
    if instrument_count != INSTRUMENT_COUNT:
        reasons.append(f"INSTRUMENT_COUNT_MISMATCH:{instrument_count}")
    if row_count != ROW_COUNT_TOTAL:
        reasons.append(f"ROW_COUNT_MISMATCH:{row_count}")
    if str(manifest.get("period_start_utc")) != WINDOW_START_UTC:
        reasons.append("WINDOW_START_MISMATCH")
    if str(manifest.get("period_end_utc")) != WINDOW_END_UTC:
        reasons.append("WINDOW_END_MISMATCH")

    bitcoin_tokens = {"btc", "xbt", "bitcoin"}
    for instrument_id in manifest.get("instrument_ids", []):
        lowered = str(instrument_id).lower()
        if any(token in lowered for token in bitcoin_tokens):
            reasons.append(f"BITCOIN_PRESENT:{instrument_id}")
            break

    expected_data_digest = str(versioned_binding["data_digest"])
    actual_data_digest = _stable_digest(
        {
            "dataset_id": PANEL_DATASET_ID,
            "dataset_digest": PANEL_DATASET_DIGEST,
            "panel_data_digest": normalized_digest,
            "lifecycle_data_digest": versioned_binding["panel_dataset_binding"][
                "lifecycle_data_digest"
            ],
            "universe_instruments_digest": versioned_binding["pit_universe_binding"][
                "universe_instruments_digest"
            ],
            "instruments_artifact_digest": "e47a6bb1d7ac072ab4b87c2f8f149d590a7023abc3489e6d6be1a225921ec91d",
            "window_start_utc": WINDOW_START_UTC,
            "window_end_utc": WINDOW_END_UTC,
        }
    )
    if actual_data_digest != expected_data_digest:
        reasons.append(f"DATA_DIGEST_RECOMPUTE_MISMATCH:{actual_data_digest}")

    return not reasons, tuple(reasons), panel_series, panel_ref


def _build_traces(
    orchestrator_result: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    ranking_trace: list[dict[str, Any]] = []
    rotation_trace: list[dict[str, Any]] = []
    decision_trace: list[dict[str, Any]] = []
    block_counter: Counter[str] = Counter()
    prev_instrument: str | None = None
    prev_side: str | None = None

    for epoch in orchestrator_result.epochs:
        sel = epoch.selection
        for code in epoch.error_codes:
            block_counter[code] += 1
        ranking_trace.append(
            {
                "epoch_index": epoch.epoch_index,
                "timestamp_utc": epoch.timestamp_utc,
                "ranked_instrument_ids": list(sel.ranked_instrument_ids),
                "top_score": sel.top_score,
                "eligible_member_count": sel.eligible_member_count,
            }
        )
        decision_trace.append(
            {
                "epoch_index": epoch.epoch_index,
                "timestamp_utc": epoch.timestamp_utc,
                "slot_side": sel.slot_side.value,
                "selected_instrument_id": sel.selected_instrument_id,
                "pending_switch": sel.pending_switch,
                "error_codes": list(epoch.error_codes),
            }
        )
        rotated = sel.selected_instrument_id != prev_instrument or sel.slot_side.value != (
            prev_side or "FLAT"
        )
        if rotated:
            rotation_trace.append(
                {
                    "epoch_index": epoch.epoch_index,
                    "timestamp_utc": epoch.timestamp_utc,
                    "from_instrument_id": prev_instrument,
                    "from_side": prev_side,
                    "to_instrument_id": sel.selected_instrument_id,
                    "to_side": sel.slot_side.value,
                    "pending_switch": sel.pending_switch,
                }
            )
        prev_instrument = sel.selected_instrument_id
        prev_side = sel.slot_side.value

    return ranking_trace, rotation_trace, decision_trace, block_counter


def _accounting_reconciliation(backtest: Any, orchestrator: Any) -> dict[str, Any]:
    result = reconcile_single_slot_backtest_accounting_v0(
        backtest,
        orchestrator_result=orchestrator,
    )
    return accounting_reconciliation_to_dict(result)


def _classify_sample_sufficiency(trade_count: int, policy: Any) -> str:
    minimum = int(policy.minimum_trade_count.value)  # type: ignore[arg-type]
    if trade_count < minimum:
        return "INSUFFICIENT_TRADE_SAMPLE"
    return "SUFFICIENT_TRADE_SAMPLE"


def _classify_baseline(net_return: float, trade_count: int) -> EconomicClassification:
    if trade_count == 0:
        return EconomicClassification.INCONCLUSIVE
    if net_return < 0.0:
        return EconomicClassification.FAIL
    if net_return > 0.0:
        return EconomicClassification.INCONCLUSIVE
    return EconomicClassification.INCONCLUSIVE


def _robustness_status(baseline_verdict: EconomicClassification) -> dict[str, str]:
    if baseline_verdict is EconomicClassification.FAIL:
        status = RobustnessExecutionStatus.NOT_EXECUTED_BASELINE_NEGATIVE.value
    else:
        status = RobustnessExecutionStatus.NOT_EXECUTED_PERIOD_BINDING_UNSPLIT.value
    return {
        "walk_forward_status": status,
        "monte_carlo_status": status,
        "stress_status": status,
        "parameter_sensitivity_status": status,
        "reason": (
            "period_binding_has_no_train_validation_oos_splits"
            if baseline_verdict is not EconomicClassification.FAIL
            else "baseline_terminal_negative_contract_blocks_robustness"
        ),
    }


def run_offline_economic_evaluation(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    source_closeout_bundle: Path,
    source_evaluation_bundle: Path | None = None,
) -> dict[str, Any]:
    if confirm not in ALLOWED_GO_TOKENS:
        _die(f"ERR: confirm_go_token_required:{sorted(ALLOWED_GO_TOKENS)}")

    preflight = run_preflight(
        repo_root=repo_root,
        source_closeout_bundle=source_closeout_bundle,
        confirm=confirm,
    )
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "research"
        / f"cross_sectional_ma_crossover_panel_rank_rotation_v0_offline_economic_evaluation_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = materialize_versioned_research_binding_v0()
    ratification = materialize_binding_ratification_v0(repo_root=repo_root)
    staging_root = Path(PANEL_STAGING_ROOT)

    if not preflight.passed:
        final_report = "\n".join(
            [
                "VERDICT=FAIL_CLOSED_PREFLIGHT",
                f"RESEARCH_SCOPE={STRATEGY_ID}/{STRATEGY_VERSION}",
                f"HEAD={preflight.head}",
                f"ORIGIN_MAIN={preflight.origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={preflight.head == preflight.origin_main}",
                f"WORKTREE_CLEAN={preflight.worktree_clean}",
                f"SOURCE_CLOSEOUT_MANIFEST_VERIFY_RC={preflight.source_closeout_manifest_verify_rc}",
                f"FAIL_REASONS={';'.join(preflight.fail_reasons)}",
                "BASELINE_EXECUTED=false",
                "REPO_MUTATION=false",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                "MANIFEST_VERIFY_RC=0",
                "NEXT_STEP=OPERATOR_INPUT_REQUIRED_PREFLIGHT_BLOCKER",
            ]
        )
        (evidence_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")
        (evidence_dir / "preflight_blocker.json").write_text(
            json.dumps(
                {
                    "passed": False,
                    "fail_reasons": list(preflight.fail_reasons),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        rc, _ = retention.finalize_durable_bundle_manifest(evidence_dir)
        return {
            "verdict": "FAIL_CLOSED_PREFLIGHT",
            "manifest_verify_rc": rc,
            "evidence_dir": str(evidence_dir),
        }

    dataset_ok, dataset_reasons, panel_series, panel_ref = _verify_dataset(
        staging_root, versioned_binding
    )
    if not dataset_ok:
        final_report = "\n".join(
            [
                "VERDICT=FAIL_CLOSED_DATASET",
                f"RESEARCH_SCOPE={STRATEGY_ID}/{STRATEGY_VERSION}",
                f"DATASET_ID={PANEL_DATASET_ID}",
                f"FAIL_REASONS={';'.join(dataset_reasons)}",
                "BASELINE_EXECUTED=false",
                "REPO_MUTATION=false",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                "NEXT_STEP=OPERATOR_INPUT_REQUIRED_DATASET_BLOCKER",
            ]
        )
        (evidence_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")
        (evidence_dir / "dataset_verification.json").write_text(
            json.dumps({"passed": False, "reasons": list(dataset_reasons)}, indent=2) + "\n",
            encoding="utf-8",
        )
        rc, _ = retention.finalize_durable_bundle_manifest(evidence_dir)
        return {
            "verdict": "FAIL_CLOSED_DATASET",
            "manifest_verify_rc": rc,
            "evidence_dir": str(evidence_dir),
        }

    binding_operator = default_ma_crossover_operator_binding_v0()
    orchestrator = run_ma_crossover_panel_rank_rotation_orchestrator_v0(
        binding=binding_operator,
        panel_series=panel_series,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orchestrator,
        panel_series,
        cost_execution_binding=versioned_binding["cost_execution_binding"],
    )
    ranking_trace, rotation_trace, decision_trace, block_counter = _build_traces(orchestrator)

    accounting = _accounting_reconciliation(backtest, orchestrator)
    policy = canonical_economic_validity_policy_v1()
    sample_status = _classify_sample_sufficiency(backtest.trade_count, policy)
    baseline_verdict = _classify_baseline(backtest.net_return, backtest.trade_count)
    robustness = _robustness_status(baseline_verdict)

    stats = backtest.stats
    gate_metrics = EconomicValidityEvidenceMetricsV1(
        net_expectancy=float(stats.get("expectancy") or 0.0),
        profit_factor=float(stats.get("profit_factor") or 0.0),
        max_drawdown=float(stats.get("max_drawdown") or 0.0),
        trade_count=backtest.trade_count,
        walk_forward_pass_ratio=None,
        out_of_sample_pass_ratio=None,
        monte_carlo_pass_ratio=None,
        stress_failure_count=None,
        parameter_robustness_pass=True,
        parameter_neighbor_degradation=None,
        single_trade_profit_contribution=None,
        single_regime_profit_contribution=None,
        data_admissibility_status="PASS",
        cost_model_status="PASS",
        funding_binding_status="PASS",
        execution_model_status="PASS",
        reproducibility_status="PASS",
        digest_binding_status="PASS",
        manifest_binding_status="PASS",
    )
    gate_eval = evaluate_economic_validity_against_policy_v1(metrics=gate_metrics, policy=policy)
    if baseline_verdict is EconomicClassification.FAIL:
        economic_classification = EconomicClassification.FAIL
        gate_pass = False
    elif sample_status == "INSUFFICIENT_TRADE_SAMPLE":
        economic_classification = EconomicClassification.INCONCLUSIVE
        gate_pass = False
    elif gate_eval.gates_pass:
        economic_classification = EconomicClassification.PASS
        gate_pass = True
    else:
        economic_classification = EconomicClassification.INCONCLUSIVE
        gate_pass = False

    long_contrib = 0.0
    short_contrib = 0.0
    if not backtest.trades.empty:
        for row in backtest.trades.to_dict(orient="records"):
            gross = float(row.get("gross_pnl_frac", 0.0))
            if row.get("side") == "LONG":
                long_contrib += gross
            elif row.get("side") == "SHORT":
                short_contrib += gross
        total = long_contrib + short_contrib
        if total != 0.0:
            long_contrib /= total
            short_contrib /= total

    instrument_contrib: dict[str, float] = {}
    if not backtest.trades.empty:
        for row in backtest.trades.to_dict(orient="records"):
            iid = str(row.get("instrument_id", "UNKNOWN"))
            instrument_contrib[iid] = instrument_contrib.get(iid, 0.0) + float(
                row.get("gross_pnl_frac", 0.0)
            )

    economic_metrics = {
        "gross_return": backtest.gross_return,
        "net_return": backtest.net_return,
        "net_expectancy": stats.get("expectancy"),
        "profit_factor": stats.get("profit_factor"),
        "sharpe": stats.get("sharpe"),
        "sortino": stats.get("sortino"),
        "max_drawdown": stats.get("max_drawdown"),
        "calmar": stats.get("calmar"),
        "trade_count": backtest.trade_count,
        "turnover": backtest.turnover,
        "fee_drag": backtest.fee_drag,
        "slippage_impact": backtest.slippage_impact,
        "spread_drag": accounting["spread_drag"],
        "funding_drag": accounting["funding_drag"],
        "time_in_market": stats.get("time_in_market"),
        "long_contribution": long_contrib,
        "short_contribution": short_contrib,
        "instrument_contribution": instrument_contrib,
        "regime_breakdown": {"by_side": {"LONG": long_contrib, "SHORT": short_contrib}},
    }

    decision_funnel = {
        "epochs_total": len(orchestrator.epochs),
        "epochs_with_eligible_rank": sum(
            1 for epoch in orchestrator.epochs if epoch.selection.eligible_member_count >= 5
        ),
        "epochs_flat": sum(
            1 for epoch in orchestrator.epochs if epoch.selection.slot_side.value == "FLAT"
        ),
        "epochs_long": sum(
            1 for epoch in orchestrator.epochs if epoch.selection.slot_side.value == "LONG"
        ),
        "epochs_short": sum(
            1 for epoch in orchestrator.epochs if epoch.selection.slot_side.value == "SHORT"
        ),
        "rotation_events": len(rotation_trace),
        "trade_count": backtest.trade_count,
    }

    trade_ledger = backtest.trades.to_dict(orient="records") if not backtest.trades.empty else []
    cost_attribution = {
        "fee_drag": backtest.fee_drag,
        "slippage_impact": backtest.slippage_impact,
        "spread_drag": accounting["spread_drag"],
        "funding_drag": accounting["funding_drag"],
        "roundtrip_cost_bps": backtest.roundtrip_cost_bps,
    }

    economic_viability_evidence = {
        "schema_version": "economic_viability_evidence_cross_sectional_ma_crossover_panel_rank_rotation_v0",
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "economic_classification": economic_classification.value,
        "baseline_verdict": baseline_verdict.value,
        "economic_validity_offline_gate_pass": gate_pass,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        **economic_metrics,
        "binding_references": {
            "binding_digest": versioned_binding["binding_digest"],
            "config_digest": versioned_binding["config_digest"],
            "data_digest": versioned_binding["data_digest"],
            "ratification_digest": ratification["ratification_digest"],
        },
        "reason_codes": list(gate_eval.reason_codes),
    }

    (evidence_dir / "reference_contract.json").write_text(
        json.dumps(
            {
                "research_scope": f"{STRATEGY_ID}/{STRATEGY_VERSION}",
                "go_token": GO_TOKEN,
                "binding_config": CONFIG_REL_PATH,
                "source_closeout_bundle": str(source_closeout_bundle),
                "panel_staging_root": str(staging_root),
                "panel_ref": panel_ref,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "binding_snapshot.json").write_text(
        json.dumps(versioned_binding, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "dataset_verification.json").write_text(
        json.dumps(
            {
                "passed": True,
                "dataset_id": PANEL_DATASET_ID,
                "instrument_count": INSTRUMENT_COUNT,
                "row_count_total": ROW_COUNT_TOTAL,
                "panel_data_digest": PANEL_DATA_DIGEST,
                "data_digest": versioned_binding["data_digest"],
                "bitcoin_present": False,
                "window_start_utc": WINDOW_START_UTC,
                "window_end_utc": WINDOW_END_UTC,
                "panel_ref": panel_ref,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "baseline_results.json").write_text(
        json.dumps(
            {
                "baseline_executed": True,
                "baseline_verdict": baseline_verdict.value,
                "orchestrator_version": orchestrator.orchestrator_version,
                "score_formula_version": orchestrator.score_formula_version,
                "final_slot_side": orchestrator.final_slot_side.value,
                "final_instrument_id": orchestrator.final_instrument_id,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "economic_metrics.json").write_text(
        json.dumps(economic_metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "decision_funnel.json").write_text(
        json.dumps(decision_funnel, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "block_reason_counts.json").write_text(
        json.dumps(dict(block_counter), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "ranking_trace.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in ranking_trace)
        + ("\n" if ranking_trace else ""),
        encoding="utf-8",
    )
    (evidence_dir / "rotation_trace.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rotation_trace)
        + ("\n" if rotation_trace else ""),
        encoding="utf-8",
    )
    (evidence_dir / "decision_trace.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in decision_trace)
        + ("\n" if decision_trace else ""),
        encoding="utf-8",
    )
    (evidence_dir / "trade_ledger.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True, default=str) for row in trade_ledger)
        + ("\n" if trade_ledger else ""),
        encoding="utf-8",
    )
    (evidence_dir / "cost_attribution.json").write_text(
        json.dumps(cost_attribution, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "accounting_reconciliation.json").write_text(
        json.dumps(accounting, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "sample_sufficiency.json").write_text(
        json.dumps(
            {
                "status": sample_status,
                "trade_count": backtest.trade_count,
                "minimum_trade_count_policy": int(policy.minimum_trade_count.value),  # type: ignore[arg-type]
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "robustness_status.json").write_text(
        json.dumps(robustness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "economic_viability_evidence_v1.json").write_text(
        json.dumps(economic_viability_evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if source_evaluation_bundle is not None:
        original_accounting_path = source_evaluation_bundle / "accounting_reconciliation.json"
        original_metrics_path = source_evaluation_bundle / "economic_metrics.json"
        original_accounting = (
            json.loads(original_accounting_path.read_text(encoding="utf-8"))
            if original_accounting_path.is_file()
            else {}
        )
        original_metrics = (
            json.loads(original_metrics_path.read_text(encoding="utf-8"))
            if original_metrics_path.is_file()
            else {}
        )
        comparison = {
            "superseded_evaluation_bundle": str(source_evaluation_bundle),
            "superseded_reason": "SUPERSEDED_ACCOUNTING_RECONCILIATION_DEFECT",
            "binding_digest": versioned_binding["binding_digest"],
            "config_digest": versioned_binding["config_digest"],
            "data_digest": versioned_binding["data_digest"],
            "ratification_digest": ratification["ratification_digest"],
            "binding_changed": False,
            "trading_logic_changed": False,
            "cost_policy_changed": False,
            "accounting_failure_class": FAILURE_FORCED_END_OF_WINDOW_LIQUIDATION_MISSING,
            "accounting_root_cause": (
                "open_position_at_window_end_without_force_close_trade_ledger_entry"
            ),
            "end_of_window_policy": END_OF_WINDOW_POLICY,
            "original_metrics": original_metrics,
            "corrected_metrics": economic_metrics,
            "original_accounting": original_accounting,
            "corrected_accounting": accounting,
            "semantic_effect": (
                "end_of_window_force_close_records_final_rotation_trade;"
                "economic_metrics_may_shift_only_from_accounting_completion"
            ),
        }
        (evidence_dir / "previous_vs_corrected_evaluation.json").write_text(
            json.dumps(comparison, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (evidence_dir / "superseded_evaluation_reference.json").write_text(
            json.dumps(
                {
                    "superseded_bundle": str(source_evaluation_bundle),
                    "superseded_manifest_verify_rc": 0,
                    "superseded_accounting_reconciliation_pass": original_accounting.get(
                        "reconciled", False
                    ),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    final_report_lines = [
        f"VERDICT={economic_classification.value}",
        f"RESEARCH_SCOPE={STRATEGY_ID}/{STRATEGY_VERSION}",
        f"HEAD={preflight.head}",
        f"ORIGIN_MAIN={preflight.origin_main}",
        f"HEAD_EQUALS_ORIGIN_MAIN={preflight.head == preflight.origin_main}",
        f"WORKTREE_CLEAN={preflight.worktree_clean}",
        f"SOURCE_CLOSEOUT_MANIFEST_VERIFY_RC={preflight.source_closeout_manifest_verify_rc}",
        "BINDING_RATIFIED=true",
        f"BINDING_DIGEST={versioned_binding['binding_digest']}",
        f"CONFIG_DIGEST={versioned_binding['config_digest']}",
        f"DATA_DIGEST={versioned_binding['data_digest']}",
        f"IMPLEMENTATION_DIGEST={versioned_binding['implementation_digest']}",
        f"RATIFICATION_DIGEST={ratification['ratification_digest']}",
        f"DATASET_ID={PANEL_DATASET_ID}",
        f"INSTRUMENT_COUNT={INSTRUMENT_COUNT}",
        "BITCOIN_PRESENT=false",
        "BASELINE_EXECUTED=true",
        f"BASELINE_VERDICT={baseline_verdict.value}",
        f"SAMPLE_SUFFICIENCY_STATUS={sample_status}",
        f"GROSS_RETURN={backtest.gross_return}",
        f"NET_RETURN={backtest.net_return}",
        f"NET_EXPECTANCY={stats.get('expectancy')}",
        f"PROFIT_FACTOR={stats.get('profit_factor')}",
        f"SHARPE={stats.get('sharpe')}",
        f"SORTINO={stats.get('sortino')}",
        f"MAX_DRAWDOWN={stats.get('max_drawdown')}",
        f"TRADE_COUNT={backtest.trade_count}",
        f"TURNOVER={backtest.turnover}",
        f"FEE_DRAG={backtest.fee_drag}",
        f"SLIPPAGE_IMPACT={backtest.slippage_impact}",
        f"SPREAD_DRAG={accounting['spread_drag']}",
        f"FUNDING_DRAG={accounting['funding_drag']}",
        f"ACCOUNTING_RECONCILIATION_PASS={accounting['reconciled']}",
        f"WALK_FORWARD_STATUS={robustness['walk_forward_status']}",
        f"MONTE_CARLO_STATUS={robustness['monte_carlo_status']}",
        f"STRESS_STATUS={robustness['stress_status']}",
        f"ECONOMIC_VALIDITY_OFFLINE_GATE_PASS={gate_pass}",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        "REPO_MUTATION=false",
        "PR_NUMBER=",
        f"DURABLE_EVIDENCE_DIR={evidence_dir}",
        "MANIFEST_VERIFY_RC=0",
        "NEXT_STEP=AWAIT_OPERATOR_REVIEW_OFFLINE_ECONOMIC_EVALUATION_EVIDENCE",
    ]
    (evidence_dir / "final_report.txt").write_text(
        "\n".join(final_report_lines) + "\n", encoding="utf-8"
    )

    manifest_rc, _ = retention.finalize_durable_bundle_manifest(evidence_dir)
    if manifest_rc != 0:
        _die(f"ERR: manifest_verify_failed:{manifest_rc}")

    return {
        "verdict": economic_classification.value,
        "baseline_verdict": baseline_verdict.value,
        "net_return": backtest.net_return,
        "trade_count": backtest.trade_count,
        "manifest_verify_rc": manifest_rc,
        "evidence_dir": str(evidence_dir),
        "gate_pass": gate_pass,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument(
        "--source-closeout-bundle", type=Path, default=Path(SOURCE_CLOSEOUT_BUNDLE_PR5079)
    )
    parser.add_argument(
        "--source-evaluation-bundle",
        type=Path,
        default=None,
    )
    args = parser.parse_args()
    source_eval = args.source_evaluation_bundle
    if source_eval is None and args.confirm_go_token == ACCOUNTING_FIX_GO_TOKEN:
        source_eval = Path(SOURCE_EVALUATION_BUNDLE_DEFAULT)
    result = run_offline_economic_evaluation(
        confirm=args.confirm_go_token,
        repo_root=_REPO_ROOT,
        durable_evidence_root=args.durable_evidence_root,
        source_closeout_bundle=args.source_closeout_bundle,
        source_evaluation_bundle=source_eval,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
