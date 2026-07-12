#!/usr/bin/env python3
"""Ops runner for cross-sectional lead-lag diffusion v0 offline economic evaluation.

Two bounded modes:
- Infrastructure/dry-run: GO_...EXECUTION_INFRASTRUCTURE_IMPLEMENTATION_V0
- Full evaluation dispatch: GO_...OFFLINE_ECONOMIC_EVALUATION_REEVALUATION_V0

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
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN,
    EXECUTION_VERSION,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    REASON_FULL_CANONICAL_PARITY_NOT_PROVEN,
    REEVALUATION_GO_TOKEN,
    RUNTIME_EFFECT,
    SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
    SYSTEM_EVIDENCE_MV2_PATH_MODE,
    entrypoint_result_to_dict,
    execution_result_to_dict,
    load_evaluation_path_parity_status_v0,
    load_ohlcv_panel_series_for_backtest,
    load_versioned_hypothesis_binding_v0,
    materialize_infrastructure_summary_v0,
    materialize_preexecution_fail_closed_block_v0,
    materialize_runner_envelope_v0,
    materialize_system_evidence_mv2_offline_economic_evaluation_binding_v0,
    resolve_dispatch_go_token_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_full_offline_economic_evaluation_v0,
    run_mv2_system_evidence_wiring_dispatch_v0,
    validate_entry_point_go_token_v0,
    verify_execution_start_state_v0,
    verify_full_evaluation_precheck_v1,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (  # noqa: E402
    build_synthetic_panel_series_v0,
)

INFRASTRUCTURE_GO = INFRASTRUCTURE_GO_TOKEN
REEVALUATION_GO = REEVALUATION_GO_TOKEN
MAX_RUNTIME_SECONDS = 1500
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)
INFRASTRUCTURE_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_"
    "ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_V0"
)
FULL_EVAL_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_"
    "ECONOMIC_EVALUATION_REEVALUATION_V0"
)
EXECUTION_V0_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_"
    "ECONOMIC_EVALUATION_EXECUTION_V0"
)
FULL_EVALUATION_DISPATCH_GO_TOKENS = frozenset(
    {GO_TOKEN, REEVALUATION_GO_TOKEN, SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN}
)
MV2_WIRING_ADAPTER_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_V0_MV2_RESEARCH_BACKTEST_WIRING_BOUNDARY_ADAPTER_"
    "IMPLEMENTATION_V0"
)
MV2_WIRING_ADAPTER_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_LEAD_LAG_V0_MV2_RESEARCH_BACKTEST_WIRING_"
    "BOUNDARY_ADAPTER_IMPLEMENTATION_V0"
)
MV2_BINDING_SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_LEAD_LAG_V0_SYSTEM_EVIDENCE_MV2_OFFLINE_"
    "ECONOMIC_EVALUATION_BINDING_V0"
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
        / (
            "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
            f"evaluation_execution_infrastructure_implementation_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    ratification = materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    panel_series = build_synthetic_panel_series_v0()
    entrypoint = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=staging_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        go_token=INFRASTRUCTURE_GO,
    )
    entrypoint_payload = entrypoint_result_to_dict(entrypoint)
    summary = materialize_infrastructure_summary_v0(
        ratification=ratification,
        readiness=type(
            "ReadinessProxy",
            (),
            {
                "execution_infrastructure_complete": entrypoint.precheck_passed,
                "panel_wiring_complete": True,
                "bound_dataset_materialized": entrypoint.bound_dataset_materialized,
                "dataset_period_match": entrypoint.dataset_period_match,
                "panel_data_digest": entrypoint.panel_data_digest,
                "status": entrypoint.status,
                "reason_codes": entrypoint.reason_codes,
                "smoke_backtest_net_return": None,
                "smoke_trade_count": None,
            },
        )(),
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
                f"SCOPE_CLASSIFICATION={INFRASTRUCTURE_SCOPE_CLASSIFICATION}",
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
        "process_classification": INFRASTRUCTURE_SCOPE_CLASSIFICATION,
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
    _guard_timeout(start_monotonic)
    return payload


def _emit_preexecution_block(*, block: dict[str, Any]) -> None:
    for key, value in block.items():
        print(f"{key}={str(value).lower() if isinstance(value, bool) else value}", file=sys.stderr)


def _write_preexecution_block_files(bundle_dir: Path, *, block: dict[str, Any]) -> None:
    lines = [f"{key}={value}\n" for key, value in block.items()]
    (bundle_dir / "PREEXECUTION_BLOCK.txt").write_text("".join(lines), encoding="utf-8")
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )


def _resolve_full_evaluation_scope_classification(confirm: str) -> str:
    if confirm == GO_TOKEN:
        return EXECUTION_V0_SCOPE_CLASSIFICATION
    if confirm == REEVALUATION_GO_TOKEN:
        return FULL_EVAL_SCOPE_CLASSIFICATION
    return MV2_BINDING_SCOPE_CLASSIFICATION


def _resolve_full_evaluation_bundle_suffix(confirm: str) -> str:
    if confirm == GO_TOKEN:
        return "evaluation_execution_v0"
    if confirm == REEVALUATION_GO_TOKEN:
        return "evaluation_reevaluation_v0"
    return "evaluation_mv2_binding_v0"


def run_bounded_full_evaluation_dispatch_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    entry_ok, _ = validate_entry_point_go_token_v0(confirm)
    if not entry_ok or confirm not in FULL_EVALUATION_DISPATCH_GO_TOKENS:
        _die(
            f"ERR:confirm_go_token_required:{'|'.join(sorted(FULL_EVALUATION_DISPATCH_GO_TOKENS))}"
        )

    requested_go = confirm
    dispatched_go = resolve_dispatch_go_token_v0(requested_go)
    if dispatched_go != requested_go:
        _die("ERR:dispatch_go_token_rewrite_forbidden")

    full_chain_wired, parity_pass = load_evaluation_path_parity_status_v0(_REPO_ROOT)
    runner_envelope = materialize_runner_envelope_v0(
        requested_operator_go=requested_go,
        dispatched_go_token=dispatched_go,
        dispatch_rc=0,
        preexecution_parity_guard_pass=full_chain_wired and parity_pass,
        full_canonical_chain_wired=full_chain_wired,
        backtest_runtime_decision_parity_pass=parity_pass,
    )

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / (
            "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
            f"{_resolve_full_evaluation_bundle_suffix(confirm)}_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)
    scope_classification = _resolve_full_evaluation_scope_classification(confirm)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    ratification = materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )

    precheck_ok, precheck_reasons, _ = verify_full_evaluation_precheck_v1(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        go_token=dispatched_go,
        require_execution_go=True,
        runner_envelope=runner_envelope,
        materialize_dataset=False,
    )

    (bundle_dir / "PREFLIGHT.txt").write_text(
        "\n".join(
            [
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_HEAD_BEFORE={primary_before['head']}",
                f"START_STATE_VALID={start_state.valid}",
                f"REQUESTED_OPERATOR_GO={requested_go}",
                f"DISPATCH_GO_TOKEN={dispatched_go}",
                f"GO_TOKEN={dispatched_go}",
                f"SCOPE_CLASSIFICATION={scope_classification}",
                f"FULL_CANONICAL_CHAIN_WIRED={str(full_chain_wired).lower()}",
                f"BACKTEST_RUNTIME_DECISION_PARITY_PASS={str(parity_pass).lower()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "RUNNER_ENVELOPE.json").write_text(
        json.dumps(
            {
                "requested_operator_go": runner_envelope.requested_operator_go,
                "dispatched_go_token": runner_envelope.dispatched_go_token,
                "dispatch_rc": runner_envelope.dispatch_rc,
                "dispatch_successful": runner_envelope.dispatch_successful,
                "preexecution_parity_guard_pass": runner_envelope.preexecution_parity_guard_pass,
                "full_canonical_chain_wired": runner_envelope.full_canonical_chain_wired,
                "backtest_runtime_decision_parity_pass": (
                    runner_envelope.backtest_runtime_decision_parity_pass
                ),
                "envelope_digest": runner_envelope.envelope_digest,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    if not precheck_ok:
        block = materialize_preexecution_fail_closed_block_v0(
            block_reason=BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN
            if REASON_FULL_CANONICAL_PARITY_NOT_PROVEN in precheck_reasons
            else "PREEXECUTION_GUARD_FAIL_CLOSED",
        )
        _emit_preexecution_block(block=block)
        _write_preexecution_block_files(bundle_dir, block=block)
        (bundle_dir / "PRECHECK_RESULT.json").write_text(
            json.dumps(
                {
                    "precheck_passed": False,
                    "reason_codes": list(precheck_reasons),
                    **block,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
        payload: dict[str, Any] = {
            "verdict": "FAIL_CLOSED_PRECHECK",
            "process_classification": scope_classification,
            "execution_version": EXECUTION_VERSION,
            "origin_main": origin_main,
            "start_state_valid": start_state.valid,
            "requested_operator_go": requested_go,
            "dispatched_go_token": dispatched_go,
            "precheck_passed": False,
            "precheck_reason_codes": list(precheck_reasons),
            "economic_evaluation_executed": False,
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
            "primary_worktree": str(primary_worktree),
            "staging_root": str(staging_root),
            "durable_evidence_path": str(bundle_dir),
            "manifest_verify_rc": manifest_rc,
            "manifest_verify_msg": manifest_msg,
            "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
            **block,
        }
        (bundle_dir / "EXECUTION_RESULT.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _guard_timeout(start_monotonic)
        raise SystemExit(1)

    panel_series = load_ohlcv_panel_series_for_backtest(staging_root)
    evaluation = run_full_offline_economic_evaluation_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=staging_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        go_token=dispatched_go,
        runner_envelope=runner_envelope,
    )
    evaluation_payload = execution_result_to_dict(evaluation)
    economic_executed = evaluation.economic_evaluation_executed

    (bundle_dir / "FULL_EVALUATION_RESULT.json").write_text(
        json.dumps(evaluation_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        f"ECONOMIC_EVALUATION_EXECUTED={'true' if economic_executed else 'false'}\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload = {
        "verdict": evaluation_payload["status"],
        "process_classification": scope_classification,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
        "requested_operator_go": requested_go,
        "dispatched_go_token": dispatched_go,
        "evaluation": evaluation_payload,
        "economic_evaluation_executed": economic_executed,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree": str(primary_worktree),
        "staging_root": str(staging_root),
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


def run_full_evaluation_dispatch_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    return run_bounded_full_evaluation_dispatch_v0(
        confirm=confirm,
        durable_evidence_root=durable_evidence_root,
        primary_worktree=primary_worktree,
        staging_root=staging_root,
    )


def run_mv2_wiring_adapter_dispatch_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != MV2_WIRING_ADAPTER_GO_TOKEN:
        _die(f"ERR:confirm_go_token_required:{MV2_WIRING_ADAPTER_GO_TOKEN}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (
            "cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_"
            f"adapter_implementation_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    ratification = materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    panel_series = load_ohlcv_panel_series_for_backtest(staging_root)
    dispatch = run_mv2_system_evidence_wiring_dispatch_v0(
        repo_root=_REPO_ROOT,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        go_token=confirm,
    )

    (bundle_dir / "PREFLIGHT.txt").write_text(
        "\n".join(
            [
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_HEAD_BEFORE={primary_before['head']}",
                f"GO_TOKEN={confirm}",
                f"SCOPE_CLASSIFICATION={MV2_WIRING_ADAPTER_SCOPE_CLASSIFICATION}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "MV2_WIRING_ADAPTER_DISPATCH.json").write_text(
        json.dumps(dispatch, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload: dict[str, Any] = {
        "verdict": dispatch["adapter"]["status"],
        "process_classification": MV2_WIRING_ADAPTER_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
        "dispatch": dispatch,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree": str(primary_worktree),
        "staging_root": str(staging_root),
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


def run_system_evidence_mv2_binding_dispatch_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN:
        _die(f"ERR:confirm_go_token_required:{SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / (
            "cross_sectional_futures_lead_lag_v0_system_evidence_mv2_offline_economic_"
            f"evaluation_binding_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    ratification = materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    binding_contract = materialize_system_evidence_mv2_offline_economic_evaluation_binding_v0()
    full_chain_wired, parity_pass = load_evaluation_path_parity_status_v0(_REPO_ROOT)
    runner_envelope = materialize_runner_envelope_v0(
        requested_operator_go=confirm,
        dispatched_go_token=resolve_dispatch_go_token_v0(confirm),
        dispatch_rc=0,
        preexecution_parity_guard_pass=full_chain_wired and parity_pass,
        full_canonical_chain_wired=full_chain_wired,
        backtest_runtime_decision_parity_pass=parity_pass,
    )
    precheck_ok, precheck_reasons, _ = verify_full_evaluation_precheck_v1(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        go_token=confirm,
        require_execution_go=True,
        runner_envelope=runner_envelope,
        materialize_dataset=False,
    )
    if not precheck_ok:
        block = materialize_preexecution_fail_closed_block_v0()
        _emit_preexecution_block(block=block)
        _write_preexecution_block_files(bundle_dir, block=block)
        (bundle_dir / "PRECHECK_RESULT.json").write_text(
            json.dumps(
                {"precheck_passed": False, "reason_codes": list(precheck_reasons), **block},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
        payload = {
            "verdict": "FAIL_CLOSED_PRECHECK",
            "process_classification": MV2_BINDING_SCOPE_CLASSIFICATION,
            "execution_version": EXECUTION_VERSION,
            "origin_main": origin_main,
            "start_state_valid": start_state.valid,
            "precheck_passed": False,
            "precheck_reason_codes": list(precheck_reasons),
            "economic_evaluation_executed": False,
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
            "primary_worktree": str(primary_worktree),
            "staging_root": str(staging_root),
            "durable_evidence_path": str(bundle_dir),
            "manifest_verify_rc": manifest_rc,
            "manifest_verify_msg": manifest_msg,
            "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
            **block,
        }
        (bundle_dir / "EXECUTION_RESULT.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _guard_timeout(start_monotonic)
        raise SystemExit(1)

    panel_series = load_ohlcv_panel_series_for_backtest(staging_root)
    evaluation = run_full_offline_economic_evaluation_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=staging_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        go_token=confirm,
        runner_envelope=runner_envelope,
    )
    evaluation_payload = execution_result_to_dict(evaluation)
    economic_executed = evaluation.economic_evaluation_executed

    (bundle_dir / "PREFLIGHT.txt").write_text(
        "\n".join(
            [
                f"ORIGIN_MAIN={origin_main}",
                f"PRIMARY_HEAD_BEFORE={primary_before['head']}",
                f"START_STATE_VALID={start_state.valid}",
                f"GO_TOKEN={confirm}",
                f"SCOPE_CLASSIFICATION={MV2_BINDING_SCOPE_CLASSIFICATION}",
                f"EVALUATION_PATH_MODE={SYSTEM_EVIDENCE_MV2_PATH_MODE}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "BINDING_CONTRACT.json").write_text(
        json.dumps(binding_contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "MV2_BINDING_EVALUATION_RESULT.json").write_text(
        json.dumps(evaluation_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        f"ECONOMIC_EVALUATION_EXECUTED={'true' if economic_executed else 'false'}\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload: dict[str, Any] = {
        "verdict": evaluation_payload["status"],
        "process_classification": MV2_BINDING_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
        "evaluation_path_mode": SYSTEM_EVIDENCE_MV2_PATH_MODE,
        "binding_contract": binding_contract,
        "evaluation": evaluation_payload,
        "economic_evaluation_executed": economic_executed,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree": str(primary_worktree),
        "staging_root": str(staging_root),
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    args = parser.parse_args()

    if args.confirm == INFRASTRUCTURE_GO:
        result = run_execution_infrastructure_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm in FULL_EVALUATION_DISPATCH_GO_TOKENS:
        result = run_bounded_full_evaluation_dispatch_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm == MV2_WIRING_ADAPTER_GO_TOKEN:
        result = run_mv2_wiring_adapter_dispatch_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif args.confirm == SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN:
        result = run_system_evidence_mv2_binding_dispatch_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    else:
        _die(
            "ERR:confirm_go_token_required:"
            f"{INFRASTRUCTURE_GO}|{GO_TOKEN}|{REEVALUATION_GO}|{MV2_WIRING_ADAPTER_GO_TOKEN}|"
            f"{SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN}"
        )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
