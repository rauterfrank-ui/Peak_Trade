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
    EXECUTION_VERSION,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    REEVALUATION_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    execution_result_to_dict,
    load_ohlcv_panel_series_for_backtest,
    load_versioned_hypothesis_binding_v0,
    materialize_infrastructure_summary_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_full_offline_economic_evaluation_v0,
    verify_execution_start_state_v0,
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


def run_full_evaluation_dispatch_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != REEVALUATION_GO:
        _die(f"ERR:confirm_go_token_required:{REEVALUATION_GO}")
    if confirm == GO_TOKEN:
        _die("ERR:execution_go_not_authorized_for_full_evaluation_use_reevaluation_go")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "research"
        / (
            "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
            f"evaluation_reevaluation_v0_{ts_slug}"
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
    evaluation = run_full_offline_economic_evaluation_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=staging_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        go_token=confirm,
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
                f"SCOPE_CLASSIFICATION={FULL_EVAL_SCOPE_CLASSIFICATION}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "FULL_EVALUATION_RESULT.json").write_text(
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
        "process_classification": FULL_EVAL_SCOPE_CLASSIFICATION,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "start_state_valid": start_state.valid,
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
    elif args.confirm == REEVALUATION_GO:
        result = run_full_evaluation_dispatch_v0(
            confirm=args.confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    else:
        _die(f"ERR:confirm_go_token_required:{INFRASTRUCTURE_GO}|{REEVALUATION_GO}")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
