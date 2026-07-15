#!/usr/bin/env python3
"""Ops runner for cross-sectional pairwise spillover v1 offline economic evaluation.

Bounded infrastructure mode only:
GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_IMPLEMENTATION_V0

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
    EXECUTION_GO_TOKEN,
    EXECUTION_VERSION,
    IMPLEMENTATION_GO_TOKEN,
    RUNTIME_EFFECT,
    InfrastructureReadinessResultV0,
    InfrastructureTerminalStatus,
    entrypoint_result_to_dict,
    load_authorization_ratification_v0,
    load_versioned_hypothesis_binding_v0,
    materialize_infrastructure_summary_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_execution_start_state_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (  # noqa: E402
    build_synthetic_panel_series_v0,
)

CONFIRM_GO = IMPLEMENTATION_GO_TOKEN
EXECUTION_CONFIRM_GO = EXECUTION_GO_TOKEN
MAX_RUNTIME_SECONDS = 1500
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)
SCOPE_CLASSIFICATION = (
    "BOUNDED_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_IMPLEMENTATION_V0"
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
    if confirm not in {CONFIRM_GO, EXECUTION_CONFIRM_GO}:
        _die(f"ERR:confirm_go_token_required:{CONFIRM_GO}")
    if confirm == EXECUTION_CONFIRM_GO:
        _die("ERR:full_economic_evaluation_not_authorized_in_implementation_runner")

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
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
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
        "process_classification": SCOPE_CLASSIFICATION,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    args = parser.parse_args()
    result = run_execution_infrastructure_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
