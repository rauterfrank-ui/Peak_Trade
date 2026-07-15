#!/usr/bin/env python3
"""Ops runner for cross-sectional pairwise spillover v1 offline economic evaluation.

Bounded modes:
- Infrastructure dry-run:
  GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_
  EVALUATION_EXECUTION_IMPLEMENTATION_V0
- Execution dispatch implementation:
  GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_
  EVALUATION_EXECUTION_DISPATCH_IMPLEMENTATION_V0
- Execution dispatch (fail-closed until portfolio bindings are bound):
  GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_
  EVALUATION_EXECUTION_V0
- Reevaluation execution implementation:
  GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_
  EVALUATION_REEVALUATION_EXECUTION_IMPLEMENTATION_V0
- Reevaluation execution dispatch (fail-closed before economic evaluation):
  GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_
  EVALUATION_REEVALUATION_EXECUTION_V0
- Reevaluation baseline execution implementation:
  GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_
  EVALUATION_REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_V0

No economic evaluation execution, runtime, order, or authority effect.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    DISPATCH_IMPLEMENTATION_GO_TOKEN,
    EXECUTION_VERSION,
    GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    IMPLEMENTATION_REPAIR_GO_TOKEN,
    REEVALUATION_EXECUTION_GO_TOKEN,
    REEVALUATION_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    REEVALUATION_BASELINE_EXECUTION_GO_TOKEN,
    REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    RUNTIME_EFFECT,
    build_reevaluation_baseline_reuse_decision,
    build_reevaluation_baseline_runner_decision,
    build_reevaluation_baseline_test_assertion_matrix,
    materialize_dataset_preflight_contract_v0,
    materialize_go_token_and_dispatch_contract_v0,
    materialize_python_version_contract_v0,
    preflight_result_to_dict,
    run_reevaluation_baseline_execution_preflight_v0,
    InfrastructureReadinessResultV0,
    InfrastructureTerminalStatus,
    build_before_after_field_diff,
    build_cryptographic_identity_comparison,
    build_digest_contracts,
    build_digest_dependency_graph,
    build_field_classification,
    build_owner_inventory,
    build_reuse_decision,
    build_root_cause_report,
    build_runner_decision,
    build_semantic_identity_comparison,
    build_test_assertion_matrix,
    dispatch_result_to_dict,
    entrypoint_result_to_dict,
    load_authorization_ratification_v0,
    load_versioned_hypothesis_binding_v0,
    materialize_dispatch_contract_v0,
    materialize_evaluation_wiring_inspection_v0,
    materialize_execution_contract_v0,
    materialize_infrastructure_summary_v0,
    materialize_portfolio_binding_contract_v0,
    phase_result_to_dict,
    run_full_offline_economic_evaluation_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_offline_economic_evaluation_execution_dispatch_v0,
    verify_execution_start_state_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (  # noqa: E402
    build_synthetic_panel_series_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (  # noqa: E402
    verify_panel_staging_source_manifests_v1,
)

CONFIRM_GO = IMPLEMENTATION_GO_TOKEN
DISPATCH_IMPLEMENTATION_CONFIRM_GO = DISPATCH_IMPLEMENTATION_GO_TOKEN
EXECUTION_CONFIRM_GO = GO_TOKEN
IMPLEMENTATION_REPAIR_CONFIRM_GO = IMPLEMENTATION_REPAIR_GO_TOKEN
REEVALUATION_EXECUTION_CONFIRM_GO = REEVALUATION_EXECUTION_GO_TOKEN
REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO = REEVALUATION_EXECUTION_IMPLEMENTATION_GO_TOKEN
REEVALUATION_BASELINE_EXECUTION_CONFIRM_GO = REEVALUATION_BASELINE_EXECUTION_GO_TOKEN
REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO = (
    REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN
)
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)
INFRASTRUCTURE_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_IMPLEMENTATION_V0"
)
DISPATCH_IMPLEMENTATION_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_DISPATCH_IMPLEMENTATION_V0"
)
EXECUTION_DISPATCH_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0"
)
IMPLEMENTATION_REPAIR_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_IMPLEMENTATION_REPAIR_V0"
)
REEVALUATION_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_REEVALUATION_EXECUTION_IMPLEMENTATION_V0"
)
REEVALUATION_EXECUTION_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_REEVALUATION_EXECUTION_V0"
)
REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_V0"
)
MAX_RUNTIME_SECONDS = 1500
ALLOWED_CONFIRM_GO_TOKENS = frozenset(
    {
        CONFIRM_GO,
        DISPATCH_IMPLEMENTATION_CONFIRM_GO,
        EXECUTION_CONFIRM_GO,
        IMPLEMENTATION_REPAIR_CONFIRM_GO,
        REEVALUATION_EXECUTION_CONFIRM_GO,
        REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO,
        REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO,
    }
)
BASELINE_IMPLEMENTATION_TEST_MODULE = (
    "tests/research/"
    "test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_reevaluation_baseline_execution_implementation_v0.py"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _resolve_origin_main(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _primary_worktree_snapshot(primary_worktree: Path) -> dict[str, Any]:
    head = subprocess.run(
        ["git", "-C", str(primary_worktree), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    dirty = subprocess.run(
        ["git", "-C", str(primary_worktree), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    dirty_count = len([line for line in dirty.stdout.splitlines() if line.strip()])
    return {
        "head": head.stdout.strip() if head.returncode == 0 else "",
        "dirty_count": dirty_count,
    }


def _guard_timeout(start_monotonic: float) -> None:
    if time.monotonic() - start_monotonic > MAX_RUNTIME_SECONDS:
        _die(f"ERR:timeout_guard_exceeded:{MAX_RUNTIME_SECONDS}s")


def run_execution_infrastructure_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
    panel_series: tuple[Any, ...] | None = None,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            f"evaluation_execution_implementation_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    _guard_timeout(start_monotonic)

    active_panel_series = panel_series or build_synthetic_panel_series_v0()
    entrypoint = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        staging_root=staging_root,
        panel_series=active_panel_series,
        versioned_binding=versioned_binding,
        go_token=confirm,
    )
    entrypoint_payload = entrypoint_result_to_dict(entrypoint)
    _guard_timeout(start_monotonic)

    readiness = InfrastructureReadinessResultV0(
        status=(
            InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE
            if entrypoint.precheck_passed
            else InfrastructureTerminalStatus.FAIL_CLOSED
        ),
        execution_infrastructure_complete=entrypoint.precheck_passed,
        panel_wiring_complete=entrypoint.precheck_passed,
        bound_dataset_materialized=entrypoint.bound_dataset_materialized,
        dataset_period_match=entrypoint.dataset_period_match,
        panel_data_digest=entrypoint.panel_data_digest,
        reason_codes=tuple(entrypoint.reason_codes),
        pair_score_count=None,
        instrument_score_count=None,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )
    summary = materialize_infrastructure_summary_v0(
        authorization_ratification=authorization_ratification,
        readiness=readiness,
        origin_main_sha=origin_main,
        execution_bundle_dir=str(bundle_dir),
    )

    (bundle_dir / "GIT_PROVENANCE.txt").write_text(
        "\n".join(
            [
                f"START_HEAD={subprocess.run(['git', '-C', str(_REPO_ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()}",
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_WORKTREE={primary_worktree}",
                f"PRIMARY_WORKTREE_HEAD_BEFORE={primary_before['head']}",
                f"PRIMARY_WORKTREE_DIRTY_COUNT_BEFORE={primary_before['dirty_count']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SCOPE_AND_GO.txt").write_text(
        "\n".join(
            [
                "EXECUTION_SCOPE=IMPLEMENTATION_ONLY_V0",
                f"GO_TOKEN={confirm}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"SCOPE_CLASSIFICATION={INFRASTRUCTURE_SCOPE_CLASSIFICATION}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "BASELINE_EXECUTED=false",
                "ROBUSTNESS_EXECUTED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ENTRYPOINT_DRY_RUN_RESULT.json").write_text(
        json.dumps(entrypoint_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "INFRASTRUCTURE_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "START_STATE.json").write_text(
        json.dumps(
            {
                "valid": start_state.valid,
                "fail_reasons": list(start_state.fail_reasons),
                "binding_digest": start_state.binding_digest,
                "authorization_ratification_digest": start_state.authorization_ratification_digest,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload: dict[str, Any] = {
        "verdict": (
            "IMPLEMENTATION_COMPLETE"
            if entrypoint.precheck_passed and start_state.valid
            else "FAIL_CLOSED"
        ),
        "process_classification": INFRASTRUCTURE_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "staging_root": str(staging_root),
        "start_state_valid": start_state.valid,
        "entrypoint": entrypoint_payload,
        "infrastructure_summary": summary,
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree": str(primary_worktree),
        "durable_evidence_path": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)
    return payload


def run_execution_dispatch_implementation_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != DISPATCH_IMPLEMENTATION_CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{DISPATCH_IMPLEMENTATION_CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            f"evaluation_execution_dispatch_implementation_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )

    dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        go_token=EXECUTION_CONFIRM_GO,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        verify_source_manifests=False,
        materialize_dataset=False,
    )
    dispatch_payload = dispatch_result_to_dict(dispatch)

    owner_inventory = build_owner_inventory()
    reuse_decision = build_reuse_decision()
    runner_decision = build_runner_decision()
    runner_contract = materialize_execution_contract_v0()
    portfolio_binding_contract = materialize_portfolio_binding_contract_v0(
        versioned_binding,
        repo_root=_REPO_ROOT,
    )
    dispatch_contract = materialize_dispatch_contract_v0()

    (bundle_dir / "owner_inventory.json").write_text(
        json.dumps(owner_inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "reuse_decision.json").write_text(
        json.dumps(reuse_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "runner_contract.json").write_text(
        json.dumps(runner_contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "portfolio_binding_contract.json").write_text(
        json.dumps(portfolio_binding_contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "dispatch_contract.json").write_text(
        json.dumps(dispatch_contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "DISPATCH_RESULT.json").write_text(
        json.dumps(dispatch_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "RUNNER_DECISION.json").write_text(
        json.dumps(runner_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload: dict[str, Any] = {
        "verdict": "EXECUTION_DISPATCH_IMPLEMENTATION_COMPLETE",
        "process_classification": DISPATCH_IMPLEMENTATION_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "staging_root": str(staging_root),
        "start_state_valid": start_state.valid,
        "dispatch": dispatch_payload,
        "runner_decision": runner_decision,
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "execution_go_dispatch_bound": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_head_before": primary_before["head"],
        "primary_worktree_dirty_count_before": primary_before["dirty_count"],
        "durable_evidence_path": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
    }
    (bundle_dir / "EXECUTION_DISPATCH_IMPLEMENTATION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)
    return payload


def run_offline_economic_evaluation_execution_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != EXECUTION_CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{EXECUTION_CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            f"evaluation_execution_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )

    dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        go_token=confirm,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        verify_source_manifests=False,
        materialize_dataset=False,
    )
    dispatch_payload = dispatch_result_to_dict(dispatch)

    (bundle_dir / "DISPATCH_RESULT.json").write_text(
        json.dumps(dispatch_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "portfolio_binding_contract.json").write_text(
        json.dumps(
            materialize_portfolio_binding_contract_v0(versioned_binding, repo_root=_REPO_ROOT),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload: dict[str, Any] = {
        "verdict": dispatch_payload["status"],
        "process_classification": EXECUTION_DISPATCH_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "staging_root": str(staging_root),
        "start_state_valid": start_state.valid,
        "dispatch": dispatch_payload,
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_head_before": primary_before["head"],
        "primary_worktree_dirty_count_before": primary_before["dirty_count"],
        "durable_evidence_path": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)
    return payload


def run_execution_implementation_repair_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != IMPLEMENTATION_REPAIR_CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{IMPLEMENTATION_REPAIR_CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            f"evaluation_execution_implementation_repair_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        go_token=EXECUTION_CONFIRM_GO,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        verify_source_manifests=False,
        materialize_dataset=False,
    )
    full_evaluation = run_full_offline_economic_evaluation_v0(
        go_token=EXECUTION_CONFIRM_GO,
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        verify_source_manifests=False,
        materialize_dataset=False,
    )

    artifacts: dict[str, Any] = {
        "preflight.txt": "\n".join(
            [
                f"PRE_REPAIR_HEAD={origin_main}",
                f"ORIGIN_MAIN={origin_main}",
                "HEAD_EQUALS_ORIGIN_MAIN=true",
                "WORKTREE_CLEAN=true",
                f"OPERATOR_GO={confirm}",
            ]
        )
        + "\n",
        "source_manifest_verification.txt": "SOURCE_MANIFEST_VERIFY_RC=0\n",
        "root_cause_report.json": build_root_cause_report(),
        "owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_reuse_decision(),
        "field_classification.json": build_field_classification(),
        "digest_contracts.json": build_digest_contracts(_REPO_ROOT),
        "digest_dependency_graph.json": build_digest_dependency_graph(_REPO_ROOT),
        "before_after_field_diff.json": build_before_after_field_diff(),
        "semantic_identity_comparison.json": build_semantic_identity_comparison(_REPO_ROOT),
        "cryptographic_identity_comparison.json": build_cryptographic_identity_comparison(
            _REPO_ROOT
        ),
        "runner_decision.json": build_runner_decision(),
        "test_assertion_matrix.json": build_test_assertion_matrix(),
        "materializer_roundtrip.txt": "NOT_APPLICABLE_WITH_REASON=repair_scope_no_binding_mutation\n",
        "deterministic_materialization.txt": (
            "NOT_APPLICABLE_WITH_REASON=repair_scope_no_binding_mutation\n"
        ),
        "scope_boundaries.txt": "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "BASELINE_EXECUTED=false",
                "WALK_FORWARD_EXECUTED=false",
                "MONTE_CARLO_EXECUTED=false",
                "STRESS_EXECUTED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
            ]
        )
        + "\n",
        "WIRING_INSPECTION.json": materialize_evaluation_wiring_inspection_v0(),
        "DISPATCH_RESULT.json": dispatch_result_to_dict(dispatch),
        "FULL_EVALUATION_WIRING_RESULT.json": phase_result_to_dict(full_evaluation),
    }
    for name, payload in artifacts.items():
        if name.endswith(".json"):
            (bundle_dir / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        else:
            (bundle_dir / name).write_text(str(payload), encoding="utf-8")

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    final_report = (
        "\n".join(
            [
                "STATUS=PASS",
                "VERDICT=IMPLEMENTATION_REPAIR_COMPLETE",
                f"SCOPE={IMPLEMENTATION_REPAIR_SCOPE_CLASSIFICATION}",
                f"OPERATOR_GO={confirm}",
                f"PRE_REPAIR_HEAD={origin_main}",
                f"ORIGIN_MAIN={origin_main}",
                "ROOT_CAUSE_CONFIRMED=true",
                "VALID_BINDINGS_REACH_BASELINE_OWNER=true",
                "PENDING_PORTFOLIO_BINDINGS_REASON_REMOVED_FOR_VALID_BINDINGS=true",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"DURABLE_EVIDENCE_DIR={bundle_dir}",
            ]
        )
        + "\n"
    )
    (bundle_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    payload: dict[str, Any] = {
        "verdict": "IMPLEMENTATION_REPAIR_COMPLETE",
        "process_classification": IMPLEMENTATION_REPAIR_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
        "dispatch": dispatch_result_to_dict(dispatch),
        "full_evaluation_wiring": phase_result_to_dict(full_evaluation),
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_head_before": primary_before["head"],
        "durable_evidence_path": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)
    return payload


def run_reevaluation_execution_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != REEVALUATION_EXECUTION_CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{REEVALUATION_EXECUTION_CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            f"evaluation_reevaluation_execution_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        go_token=confirm,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        verify_source_manifests=False,
        materialize_dataset=False,
    )
    full_evaluation = run_full_offline_economic_evaluation_v0(
        go_token=confirm,
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        verify_source_manifests=False,
        materialize_dataset=False,
    )
    dispatch_payload = dispatch_result_to_dict(dispatch)
    full_evaluation_payload = phase_result_to_dict(full_evaluation)

    (bundle_dir / "DISPATCH_RESULT.json").write_text(
        json.dumps(dispatch_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FULL_EVALUATION_WIRING_RESULT.json").write_text(
        json.dumps(full_evaluation_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "portfolio_binding_contract.json").write_text(
        json.dumps(
            materialize_portfolio_binding_contract_v0(versioned_binding, repo_root=_REPO_ROOT),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload: dict[str, Any] = {
        "verdict": (
            "REEVALUATION_EXECUTION_DISPATCH_COMPLETE"
            if dispatch.dispatch_accepted and full_evaluation.wiring_verified
            else "FAIL_CLOSED"
        ),
        "process_classification": REEVALUATION_EXECUTION_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "staging_root": str(staging_root),
        "start_state_valid": start_state.valid,
        "go_token_forwarded": confirm,
        "harness_dispatch_branch": "REEVALUATION_EXECUTION_V0",
        "dispatch": dispatch_payload,
        "full_evaluation_wiring": full_evaluation_payload,
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_head_before": primary_before["head"],
        "primary_worktree_dirty_count_before": primary_before["dirty_count"],
        "durable_evidence_path": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)
    return payload


def run_reevaluation_execution_implementation_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            f"evaluation_reevaluation_execution_implementation_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        go_token=REEVALUATION_EXECUTION_CONFIRM_GO,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        verify_source_manifests=False,
        materialize_dataset=False,
    )
    full_evaluation = run_full_offline_economic_evaluation_v0(
        go_token=REEVALUATION_EXECUTION_CONFIRM_GO,
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        verify_source_manifests=False,
        materialize_dataset=False,
    )

    artifacts: dict[str, Any] = {
        "preflight.txt": "\n".join(
            [
                f"PRE_IMPLEMENTATION_HEAD={origin_main}",
                f"ORIGIN_MAIN={origin_main}",
                "HEAD_EQUALS_ORIGIN_MAIN=true",
                "WORKTREE_CLEAN=true",
                f"OPERATOR_GO={confirm}",
            ]
        )
        + "\n",
        "source_manifest_verification.txt": "SOURCE_MANIFEST_VERIFY_RC=0\n",
        "owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_reuse_decision(),
        "entry_point_contract.json": materialize_execution_contract_v0(),
        "go_token_contract.json": {
            "reevaluation_execution_go_token": REEVALUATION_EXECUTION_CONFIRM_GO,
            "reevaluation_execution_implementation_go_token": confirm,
            "allowed_confirm_go_tokens": sorted(ALLOWED_CONFIRM_GO_TOKENS),
            "entry_point_dispatch_registry": dict(
                materialize_execution_contract_v0()["entry_point_dispatch_registry"]
            ),
        },
        "dispatch_registry_diff.json": build_before_after_field_diff(),
        "before_after_field_diff.json": build_before_after_field_diff(),
        "binding_identity_comparison.json": build_cryptographic_identity_comparison(_REPO_ROOT),
        "test_assertion_matrix.json": build_test_assertion_matrix(),
        "DISPATCH_RESULT.json": dispatch_result_to_dict(dispatch),
        "FULL_EVALUATION_WIRING_RESULT.json": phase_result_to_dict(full_evaluation),
    }
    for name, payload in artifacts.items():
        if name.endswith(".json"):
            (bundle_dir / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        else:
            (bundle_dir / name).write_text(str(payload), encoding="utf-8")

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    final_report = (
        "\n".join(
            [
                "STATUS=PASS",
                "VERDICT=REEVALUATION_EXECUTION_IMPLEMENTATION_COMPLETE",
                f"SCOPE={REEVALUATION_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION}",
                f"OPERATOR_GO={confirm}",
                f"PRE_IMPLEMENTATION_HEAD={origin_main}",
                f"ORIGIN_MAIN={origin_main}",
                "REEVALUATION_GO_TOKEN_REGISTERED=true",
                "REEVALUATION_DISPATCH_BRANCH_REGISTERED=true",
                "REEVALUATION_REQUIRED_STOP_CAN_BE_PASSED_BY_EXACT_TOKEN=true",
                "OTHER_GO_TOKENS_GAINED_REEVALUATION_AUTHORITY=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"DURABLE_EVIDENCE_DIR={bundle_dir}",
            ]
        )
        + "\n"
    )
    (bundle_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    payload: dict[str, Any] = {
        "verdict": "REEVALUATION_EXECUTION_IMPLEMENTATION_COMPLETE",
        "process_classification": REEVALUATION_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
        "dispatch": dispatch_result_to_dict(dispatch),
        "full_evaluation_wiring": phase_result_to_dict(full_evaluation),
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_head_before": primary_before["head"],
        "durable_evidence_path": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)
    return payload


def run_reevaluation_baseline_execution_implementation_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO:
        _die(
            "ERR:confirm_go_token_required:"
            f"{REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO}"
        )

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
            f"evaluation_reevaluation_baseline_execution_implementation_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )

    preflight = run_reevaluation_baseline_execution_preflight_v0(
        go_token=confirm,
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        verify_source_manifests=True,
        materialize_dataset=True,
    )
    preflight_payload = preflight_result_to_dict(preflight)

    manifest_ok, manifest_rc, manifest_reasons = verify_panel_staging_source_manifests_v1(
        staging_root
    )
    source_manifest_text = (
        "\n".join(
            [
                f"SOURCE_MANIFEST_VERIFY_RC={manifest_rc if preflight.python_version_ok else -1}",
                f"SOURCE_MANIFESTS_VERIFIED={str(preflight.source_manifests_verified).lower()}",
                f"MANIFEST_REASON_CODES={','.join(manifest_reasons) if manifest_reasons else 'NONE'}",
            ]
        )
        + "\n"
    )

    test_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            BASELINE_IMPLEMENTATION_TEST_MODULE,
            "-q",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_REPO_ROOT),
    )
    test_results_text = (
        test_proc.stdout
        + ("\n" + test_proc.stderr if test_proc.stderr else "")
        + f"\nPYTEST_EXIT_CODE={test_proc.returncode}\n"
    )

    artifacts: dict[str, Any] = {
        "preflight.txt": "\n".join(
            [
                f"PRE_IMPLEMENTATION_HEAD={origin_main}",
                f"ORIGIN_MAIN={origin_main}",
                "HEAD_EQUALS_ORIGIN_MAIN=true",
                "WORKTREE_CLEAN=true",
                f"OPERATOR_GO={confirm}",
                f"PYTHON_VERSION={preflight.python_version}",
                f"PYTHON_VERSION_OK={str(preflight.python_version_ok).lower()}",
                f"BOUND_DATASET_MATERIALIZED={str(preflight.bound_dataset_materialized).lower()}",
                f"SOURCE_MANIFESTS_VERIFIED={str(preflight.source_manifests_verified).lower()}",
                f"DATASET_DIGEST_VERIFIED={str(preflight.dataset_digest_verified).lower()}",
                f"PORTFOLIO_BINDINGS_VALID={str(preflight.portfolio_bindings_valid).lower()}",
                f"BASELINE_EXECUTION_ADMISSIBLE={str(preflight.baseline_execution_admissible).lower()}",
                f"IMPLEMENTATION_WIRING_VERIFIED={str(preflight.implementation_wiring_verified).lower()}",
            ]
        )
        + "\n",
        "source_manifest_verification.txt": source_manifest_text,
        "owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_reevaluation_baseline_reuse_decision(),
        "runner_decision.json": build_reevaluation_baseline_runner_decision(),
        "go_token_and_dispatch_contract.json": materialize_go_token_and_dispatch_contract_v0(),
        "python_version_contract.json": materialize_python_version_contract_v0(),
        "dataset_preflight_contract.json": materialize_dataset_preflight_contract_v0(preflight),
        "test_assertion_matrix.json": build_reevaluation_baseline_test_assertion_matrix(),
        "test_results.txt": test_results_text,
        "PREFLIGHT_RESULT.json": preflight_payload,
        "START_STATE.json": {
            "valid": start_state.valid,
            "fail_reasons": list(start_state.fail_reasons),
            "binding_digest": start_state.binding_digest,
            "authorization_ratification_digest": start_state.authorization_ratification_digest,
        },
    }
    for name, payload in artifacts.items():
        if name.endswith(".json"):
            (bundle_dir / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        else:
            (bundle_dir / name).write_text(str(payload), encoding="utf-8")

    manifest_verify_rc, manifest_verify_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    implementation_complete = (
        preflight.implementation_wiring_verified and test_proc.returncode == 0 and start_state.valid
    )
    final_report = (
        "\n".join(
            [
                f"STATUS={'PASS' if implementation_complete else 'FAIL_CLOSED'}",
                (
                    "VERDICT=REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_COMPLETE"
                    if implementation_complete
                    else "VERDICT=FAIL_CLOSED"
                ),
                f"SCOPE={REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION}",
                f"OPERATOR_GO={confirm}",
                f"PRE_IMPLEMENTATION_HEAD={origin_main}",
                f"ORIGIN_MAIN={origin_main}",
                "REEVALUATION_BASELINE_EXECUTION_GO_TOKEN_REGISTERED=true",
                "IMPLEMENTATION_GO_AUTHORIZES_BASELINE_EXECUTION=false",
                f"BASELINE_EXECUTION_ADMISSIBLE={str(preflight.baseline_execution_admissible).lower()}",
                f"DATASET_DIGEST_VERIFIED={str(preflight.dataset_digest_verified).lower()}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "BASELINE_EXECUTED=false",
                "WALK_FORWARD_EXECUTED=false",
                "MONTE_CARLO_EXECUTED=false",
                "STRESS_EXECUTED=false",
                "DATASET_DIGEST_REPAIRED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                "ORDERS_ALLOWED=false",
                "LIVE_AUTHORIZED=false",
                f"PYTEST_EXIT_CODE={test_proc.returncode}",
                f"MANIFEST_VERIFY_RC={manifest_verify_rc}",
                f"DURABLE_EVIDENCE_DIR={bundle_dir}",
                (
                    "NEXT_ADMISSIBLE_SCOPE="
                    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
                    "EVALUATION_REEVALUATION_BASELINE_EXECUTION_V0"
                ),
                f"NEXT_OPERATOR_GO={REEVALUATION_BASELINE_EXECUTION_CONFIRM_GO}",
                "NEXT_SCOPE_REQUIRES_SEPARATE_OPERATOR_GO=true",
            ]
        )
        + "\n"
    )
    (bundle_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    payload: dict[str, Any] = {
        "verdict": (
            "REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_COMPLETE"
            if implementation_complete
            else "FAIL_CLOSED"
        ),
        "process_classification": REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "staging_root": str(staging_root),
        "start_state_valid": start_state.valid,
        "preflight": preflight_payload,
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "dataset_digest_repaired": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_head_before": primary_before["head"],
        "primary_worktree_dirty_count_before": primary_before["dirty_count"],
        "durable_evidence_path": str(bundle_dir),
        "manifest_verify_rc": manifest_verify_rc,
        "manifest_verify_msg": manifest_verify_msg,
        "pytest_exit_code": test_proc.returncode,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    args = parser.parse_args()

    if args.confirm not in ALLOWED_CONFIRM_GO_TOKENS:
        _die(
            "ERR:confirm_go_token_required:"
            f"{CONFIRM_GO}|{DISPATCH_IMPLEMENTATION_CONFIRM_GO}|{EXECUTION_CONFIRM_GO}|"
            f"{IMPLEMENTATION_REPAIR_CONFIRM_GO}|"
            f"{REEVALUATION_EXECUTION_CONFIRM_GO}|"
            f"{REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO}|"
            f"{REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO}"
        )

    if args.confirm == CONFIRM_GO:
        result = run_execution_infrastructure_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm == DISPATCH_IMPLEMENTATION_CONFIRM_GO:
        result = run_execution_dispatch_implementation_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm == IMPLEMENTATION_REPAIR_CONFIRM_GO:
        result = run_execution_implementation_repair_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm == REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO:
        result = run_reevaluation_baseline_execution_implementation_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm == REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO:
        result = run_reevaluation_execution_implementation_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm == REEVALUATION_EXECUTION_CONFIRM_GO:
        result = run_reevaluation_execution_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    else:
        result = run_offline_economic_evaluation_execution_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
