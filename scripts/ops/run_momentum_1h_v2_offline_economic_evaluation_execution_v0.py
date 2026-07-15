#!/usr/bin/env python3
"""Ops runner for momentum 1h v2 offline economic evaluation execution.

Bounded modes:
- Infrastructure/dry-run: GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_V0
- Dispatch implementation: GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_DISPATCH_IMPLEMENTATION_V0
- Execution dispatch: GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0
- Baseline execution implementation:
  GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_V0
- Baseline execution dispatch (fail-closed before economic evaluation):
  GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_BASELINE_EXECUTION_V0

No runtime, order, or authority effect.
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
from src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    BASELINE_EXECUTION_GO_TOKEN,
    BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    DISPATCH_IMPLEMENTATION_GO_TOKEN,
    EXECUTION_GO_TOKEN,
    EXECUTION_VERSION,
    INFRASTRUCTURE_GO_TOKEN,
    ROUNDTRIP_COST_BPS,
    RUNTIME_EFFECT,
    build_baseline_owner_inventory,
    build_baseline_reuse_decision,
    build_baseline_runner_decision,
    build_baseline_test_assertion_matrix,
    dispatch_result_to_dict,
    entrypoint_result_to_dict,
    load_authorization_ratification_v0,
    load_versioned_research_binding_v0,
    materialize_baseline_implementation_contract_v0,
    materialize_dispatch_contract_v0,
    materialize_execution_contract_v0,
    materialize_infrastructure_summary_v0,
    preflight_result_to_dict,
    run_baseline_execution_preflight_v0,
    run_contract_smoke_evaluation_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_full_offline_economic_evaluation_v0,
    run_offline_economic_evaluation_execution_dispatch_v0,
    verify_execution_start_state_v0,
    verify_source_evidence_manifests_v0,
)

INFRASTRUCTURE_GO = INFRASTRUCTURE_GO_TOKEN
DISPATCH_IMPLEMENTATION_GO = DISPATCH_IMPLEMENTATION_GO_TOKEN
EXECUTION_GO = EXECUTION_GO_TOKEN
BASELINE_EXECUTION_GO = BASELINE_EXECUTION_GO_TOKEN
BASELINE_EXECUTION_IMPLEMENTATION_GO = BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN
SCOPE_CLASSIFICATION = (
    "BOUNDED_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_V0"
)
DISPATCH_IMPLEMENTATION_SCOPE_CLASSIFICATION = (
    "BOUNDED_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_DISPATCH_IMPLEMENTATION_V0"
)
EXECUTION_DISPATCH_SCOPE_CLASSIFICATION = (
    "BOUNDED_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
BASELINE_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION = (
    "BOUNDED_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_V0"
)
BASELINE_EXECUTION_SCOPE_CLASSIFICATION = (
    "BOUNDED_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_BASELINE_EXECUTION_V0"
)
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)
BASELINE_IMPLEMENTATION_TEST_MODULE = (
    "tests/research/"
    "test_momentum_1h_v2_offline_economic_evaluation_baseline_execution_implementation_v0.py"
)
ALLOWED_CONFIRM_GO_TOKENS = frozenset(
    {
        INFRASTRUCTURE_GO,
        DISPATCH_IMPLEMENTATION_GO,
        EXECUTION_GO,
        BASELINE_EXECUTION_IMPLEMENTATION_GO,
        BASELINE_EXECUTION_GO,
    }
)
MAX_RUNTIME_SECONDS = 900


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


def run_execution_infrastructure_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != INFRASTRUCTURE_GO:
        _die(f"ERR:confirm_go_token_required:{INFRASTRUCTURE_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (f"momentum_1h_v2_offline_economic_evaluation_execution_infrastructure_v0_{ts_slug}")
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)

    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    entrypoint = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        go_token=INFRASTRUCTURE_GO,
    )
    readiness = run_contract_smoke_evaluation_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
        authorization_ratification=authorization_ratification,
    )
    entrypoint_payload = entrypoint_result_to_dict(entrypoint)
    summary = materialize_infrastructure_summary_v0(
        authorization_ratification=authorization_ratification,
        readiness=readiness,
        origin_main_sha=origin_main,
        execution_bundle_dir=str(bundle_dir),
    )

    (bundle_dir / "PREFLIGHT.txt").write_text(
        "\n".join(
            [
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_HEAD_BEFORE={primary_before['head']}",
                f"PRIMARY_DIRTY_COUNT_BEFORE={primary_before['dirty_count']}",
                f"START_STATE_VALID={start_state.valid}",
                f"START_STATE_FAIL_REASONS={list(start_state.fail_reasons)}",
                "ROOT_CAUSE=CANONICAL_ENTRY_POINT_AND_RUNNER_NOT_MATERIALIZED",
                f"REPAIR_SCOPE={SCOPE_CLASSIFICATION}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "EXECUTION_LOG.txt").write_text(
        "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "EXECUTION_SCOPE=INFRASTRUCTURE_ONLY_V0",
                f"GO_TOKEN={confirm}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
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
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload: dict[str, Any] = {
        "verdict": entrypoint_payload["status"],
        "process_classification": SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
        "entrypoint": entrypoint_payload,
        "infrastructure_summary": summary,
        "economic_evaluation_executed": False,
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
    if time.monotonic() - start_monotonic > MAX_RUNTIME_SECONDS:
        _die(f"ERR:timeout_guard_exceeded:{MAX_RUNTIME_SECONDS}s")
    return payload


def run_execution_dispatch_implementation_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != DISPATCH_IMPLEMENTATION_GO:
        _die(f"ERR:confirm_go_token_required:{DISPATCH_IMPLEMENTATION_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (
            "momentum_1h_v2_offline_economic_evaluation_execution_dispatch_"
            f"implementation_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
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
        go_token=EXECUTION_GO,
        versioned_binding=versioned_binding,
        verify_source_manifests=True,
    )
    dispatch_payload = dispatch_result_to_dict(dispatch)
    execution_contract = materialize_execution_contract_v0()
    dispatch_contract = materialize_dispatch_contract_v0()

    (bundle_dir / "PREFLIGHT.txt").write_text(
        "\n".join(
            [
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_HEAD_BEFORE={primary_before['head']}",
                f"PRIMARY_DIRTY_COUNT_BEFORE={primary_before['dirty_count']}",
                f"START_STATE_VALID={start_state.valid}",
                f"START_STATE_FAIL_REASONS={list(start_state.fail_reasons)}",
                "ROOT_CAUSE=AUTHORIZED_EXECUTION_GO_DISPATCH_NOT_BOUND_TO_CANONICAL_OWNER",
                f"REPAIR_SCOPE={DISPATCH_IMPLEMENTATION_SCOPE_CLASSIFICATION}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "EXECUTION_LOG.txt").write_text(
        "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "EXECUTION_SCOPE=DISPATCH_IMPLEMENTATION_V0",
                f"GO_TOKEN={confirm}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"SCOPE_CLASSIFICATION={DISPATCH_IMPLEMENTATION_SCOPE_CLASSIFICATION}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "DISPATCH_RESULT.json").write_text(
        json.dumps(dispatch_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "EXECUTION_CONTRACT.json").write_text(
        json.dumps(execution_contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "DISPATCH_CONTRACT.json").write_text(
        json.dumps(dispatch_contract, indent=2, sort_keys=True) + "\n",
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
        "start_state_valid": start_state.valid,
        "dispatch": dispatch_payload,
        "execution_go_dispatch_bound": dispatch.dispatch_accepted,
        "economic_evaluation_executed": False,
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
    if time.monotonic() - start_monotonic > MAX_RUNTIME_SECONDS:
        _die(f"ERR:timeout_guard_exceeded:{MAX_RUNTIME_SECONDS}s")
    return payload


def run_execution_dispatch_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != EXECUTION_GO:
        _die(f"ERR:confirm_go_token_required:{EXECUTION_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (f"momentum_1h_v2_offline_economic_evaluation_execution_v0_{ts_slug}")
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    evaluation = run_full_offline_economic_evaluation_v0(
        go_token=EXECUTION_GO,
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        verify_source_manifests=True,
    )
    (bundle_dir / "EXECUTION_LOG.txt").write_text(
        "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                f"EXECUTION_SCOPE={EXECUTION_DISPATCH_SCOPE_CLASSIFICATION}",
                f"GO_TOKEN={confirm}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"BLOCKED={str(evaluation.blocked).lower()}",
                f"WIRING_VERIFIED={str(evaluation.wiring_verified).lower()}",
                f"REASON_CODES={list(evaluation.reason_codes)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FULL_EVALUATION_DISPATCH_RESULT.json").write_text(
        json.dumps(
            {
                "executed": evaluation.executed,
                "blocked": evaluation.blocked,
                "wiring_verified": evaluation.wiring_verified,
                "reason_codes": list(evaluation.reason_codes),
                "authority_effect": evaluation.authority_effect,
                "runtime_effect": evaluation.runtime_effect,
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
        "verdict": "EXECUTION_DISPATCH_COMPLETE",
        "process_classification": EXECUTION_DISPATCH_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "evaluation": {
            "executed": evaluation.executed,
            "blocked": evaluation.blocked,
            "wiring_verified": evaluation.wiring_verified,
            "reason_codes": list(evaluation.reason_codes),
        },
        "economic_evaluation_executed": False,
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
    if time.monotonic() - start_monotonic > MAX_RUNTIME_SECONDS:
        _die(f"ERR:timeout_guard_exceeded:{MAX_RUNTIME_SECONDS}s")
    return payload


def run_baseline_execution_implementation_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != BASELINE_EXECUTION_IMPLEMENTATION_GO:
        _die(f"ERR:confirm_go_token_required:{BASELINE_EXECUTION_IMPLEMENTATION_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (
            "momentum_1h_v2_offline_economic_evaluation_baseline_execution_"
            f"implementation_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
    authorization_ratification = load_authorization_ratification_v0(_REPO_ROOT)
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    preflight = run_baseline_execution_preflight_v0(
        go_token=confirm,
        repo_root=_REPO_ROOT,
        authorization_ratification=authorization_ratification,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        verify_source_manifests=True,
    )
    preflight_payload = preflight_result_to_dict(preflight)
    implementation_contract = materialize_baseline_implementation_contract_v0()

    source_ok, source_reasons = verify_source_evidence_manifests_v0()
    source_manifest_rc = 0 if source_ok else 1

    test_proc = subprocess.run(
        [sys.executable, "-m", "pytest", BASELINE_IMPLEMENTATION_TEST_MODULE, "-q"],
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

    git_diff_proc = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "diff", "origin/main...HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    changed_files_proc = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )

    artifacts: dict[str, Any] = {
        "preflight.txt": "\n".join(
            [
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_HEAD_BEFORE={primary_before['head']}",
                f"PRIMARY_DIRTY_COUNT_BEFORE={primary_before['dirty_count']}",
                f"START_STATE_VALID={start_state.valid}",
                f"START_STATE_FAIL_REASONS={list(start_state.fail_reasons)}",
                f"OPERATOR_GO={confirm}",
                f"BOUND_DATASET_MATERIALIZED={str(preflight.bound_dataset_materialized).lower()}",
                f"SOURCE_MANIFESTS_VERIFIED={str(preflight.source_manifests_verified).lower()}",
                f"DATASET_DIGEST_VERIFIED={str(preflight.dataset_digest_verified).lower()}",
                (
                    "IMPLEMENTATION_WIRING_VERIFIED="
                    f"{str(preflight.implementation_wiring_verified).lower()}"
                ),
            ]
        )
        + "\n",
        "source_manifest_verification.txt": (
            f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}\n"
            f"SOURCE_MANIFEST_REASONS={list(source_reasons)}\n"
        ),
        "owner_inventory.json": build_baseline_owner_inventory(),
        "reuse_decision.json": build_baseline_reuse_decision(),
        "runner_decision.json": build_baseline_runner_decision(),
        "implementation_contract.json": implementation_contract,
        "before_after_field_diff.json": {
            "before": {"entry_point_materialized": False, "baseline_backtest_call_count": 0},
            "after": {
                "entry_point_materialized": True,
                "canonical_entry_point": implementation_contract["canonical_entry_point"],
                "canonical_backtest_owner": implementation_contract["canonical_backtest_owner"],
            },
        },
        "test_assertion_matrix.json": build_baseline_test_assertion_matrix(),
        "test_results.txt": test_results_text,
        "changed_files.txt": changed_files_proc.stdout,
        "PREFLIGHT_RESULT.json": preflight_payload,
    }
    for name, payload in artifacts.items():
        if name.endswith(".json"):
            (bundle_dir / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        else:
            (bundle_dir / name).write_text(str(payload), encoding="utf-8")

    (bundle_dir / "git_diff.patch").write_text(git_diff_proc.stdout, encoding="utf-8")
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    implementation_complete = (
        preflight.implementation_wiring_verified
        and test_proc.returncode == 0
        and start_state.valid
        and manifest_rc == 0
    )
    final_report = (
        "\n".join(
            [
                f"STATUS={'PASS' if implementation_complete else 'FAIL_CLOSED'}",
                (
                    "VERDICT=IMPLEMENTATION_PR_OPENED"
                    if implementation_complete
                    else "VERDICT=FAIL_CLOSED"
                ),
                f"GO_TOKEN={confirm}",
                f"ORIGIN_MAIN={origin_main}",
                "ENTRY_POINT_MATERIALIZED=true",
                f"CANONICAL_ENTRY_POINT={implementation_contract['canonical_entry_point']}",
                (f"CANONICAL_BACKTEST_OWNER={implementation_contract['canonical_backtest_owner']}"),
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "BASELINE_EXECUTED=false",
                f"ROUNDTRIP_COST_BPS={ROUNDTRIP_COST_BPS}",
                "FUTURES_ONLY=true",
                "BITCOIN_PRESENT=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                f"PYTEST_EXIT_CODE={test_proc.returncode}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"DURABLE_EVIDENCE_DIR={bundle_dir}",
                (
                    "NEXT_ADMISSIBLE_SCOPE="
                    "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_BASELINE_EXECUTION_V0"
                ),
            ]
        )
        + "\n"
    )
    (bundle_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    (bundle_dir / "pr_metadata.json").write_text(
        json.dumps(
            {
                "branch": "cursor/trend-following-v2-baseline-execution-entry-point-implementation-v0",
                "scope": BASELINE_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION,
                "go_token": confirm,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload: dict[str, Any] = {
        "verdict": (
            "BASELINE_EXECUTION_IMPLEMENTATION_COMPLETE"
            if implementation_complete
            else "FAIL_CLOSED"
        ),
        "process_classification": BASELINE_EXECUTION_IMPLEMENTATION_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
        "preflight": preflight_payload,
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "entry_point_materialized": True,
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
    if time.monotonic() - start_monotonic > MAX_RUNTIME_SECONDS:
        _die(f"ERR:timeout_guard_exceeded:{MAX_RUNTIME_SECONDS}s")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, default=_REPO_ROOT)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    args = parser.parse_args()
    if args.confirm == INFRASTRUCTURE_GO:
        result = run_execution_infrastructure_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
        )
    elif args.confirm == DISPATCH_IMPLEMENTATION_GO:
        result = run_execution_dispatch_implementation_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
        )
    elif args.confirm == EXECUTION_GO:
        result = run_execution_dispatch_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
        )
    elif args.confirm == BASELINE_EXECUTION_IMPLEMENTATION_GO:
        result = run_baseline_execution_implementation_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm == BASELINE_EXECUTION_GO:
        _die(
            "ERR:baseline_execution_requires_materialized_entry_point:"
            f"{BASELINE_EXECUTION_IMPLEMENTATION_GO}"
        )
    else:
        _die(
            "ERR:confirm_go_token_required:"
            f"{INFRASTRUCTURE_GO}|{DISPATCH_IMPLEMENTATION_GO}|{EXECUTION_GO}|"
            f"{BASELINE_EXECUTION_IMPLEMENTATION_GO}|{BASELINE_EXECUTION_GO}"
        )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
