#!/usr/bin/env python3
"""Infrastructure recovery runner for funding-rate carry v0 execution.

Validates bound research binding, ensures funding-panel staging exists,
runs full-entrypoint dry-run, and writes durable implementation evidence.
No economic evaluation execution is performed.
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
from scripts.ops.materialize_cross_sectional_funding_rate_carry_v0_bound_panel_funding_dataset_v0 import (  # noqa: E402
    DEFAULT_STAGING_ROOT,
    materialize_bound_panel_funding_dataset_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    load_ohlcv_panel_series_for_backtest,
    load_versioned_research_binding_v0,
    materialization_result_to_dict,
    materialize_infrastructure_summary_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_execution_start_state_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_funding_carry_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    MaterializationTerminalStatus,
    materialize_bound_funding_panel_dataset_v0,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
MAX_RUNTIME_SECONDS = 1500
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
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
        _die(f"ERR: timeout_guard_exceeded:{MAX_RUNTIME_SECONDS}s")


def run_execution_infrastructure_recovery_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
    skip_fetch: bool = False,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / f"bounded_cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_recovery_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
    ratification = materialize_funding_carry_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    _guard_timeout(start_monotonic)

    funding_materialize_result = materialize_bound_panel_funding_dataset_v0(
        confirm=confirm,
        staging_root=staging_root,
        skip_fetch=skip_fetch,
    )
    _guard_timeout(start_monotonic)

    materialization = materialize_bound_funding_panel_dataset_v0(
        staging_root,
        period_binding=versioned_binding["period_binding"],
        expected_data_digest=versioned_binding["data_digest"],
    )
    _guard_timeout(start_monotonic)

    entrypoint_payload: dict[str, Any] | None = None
    if materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        panel_series = load_ohlcv_panel_series_for_backtest(staging_root)
        entrypoint = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=_REPO_ROOT,
            ratification=ratification,
            staging_root=staging_root,
            panel_series=panel_series,
            versioned_binding=versioned_binding,
            go_token=confirm,
        )
        entrypoint_payload = entrypoint_result_to_dict(entrypoint)
    _guard_timeout(start_monotonic)

    from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
        InfrastructureReadinessResultV0,
        InfrastructureTerminalStatus,
    )

    readiness = InfrastructureReadinessResultV0(
        status=(
            InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE
            if materialization.status
            is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
            else InfrastructureTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE
        ),
        execution_infrastructure_complete=True,
        panel_wiring_complete=True,
        bound_dataset_materialized=(
            materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        ),
        dataset_period_match=(
            materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        ),
        panel_data_digest=materialization.panel_data_digest,
        reason_codes=materialization.reason_codes,
        smoke_backtest_net_return=None,
        smoke_trade_count=None,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )
    summary = materialize_infrastructure_summary_v0(
        ratification=ratification,
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
        f"GO_TOKEN={CONFIRM_GO}\nGO_TOKEN_CONSUMPTION=CONSUMED_ONCE\n"
        "EXECUTION_SCOPE=INFRASTRUCTURE_RECOVERY_DRY_RUN_ONLY\n",
        encoding="utf-8",
    )
    (bundle_dir / "FUNDING_PANEL_MATERIALIZATION_RESULT.json").write_text(
        json.dumps(funding_materialize_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "DATASET_MATERIALIZATION_RESULT.json").write_text(
        json.dumps(materialization_result_to_dict(materialization), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "INFRASTRUCTURE_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if entrypoint_payload is not None:
        (bundle_dir / "ENTRYPOINT_DRY_RUN_RESULT.json").write_text(
            json.dumps(entrypoint_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        "ECONOMIC_EVALUATION_EXECUTED=false\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    _guard_timeout(start_monotonic)

    return {
        "verdict": (
            "INFRASTRUCTURE_RECOVERY_PASS"
            if materialization.status
            is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
            else "INFRASTRUCTURE_RECOVERY_FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"
        ),
        "bundle_dir": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "start_state_valid": start_state.valid,
        "materialization_status": materialization.status.value,
        "infrastructure_status": readiness.status.value,
        "entrypoint_status": entrypoint_payload.get("status") if entrypoint_payload else "NOT_RUN",
        "panel_data_digest": materialization.panel_data_digest,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
        "timeout_guard_seconds": MAX_RUNTIME_SECONDS,
        "primary_worktree": str(primary_worktree),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()
    result = run_execution_infrastructure_recovery_v0(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
        skip_fetch=args.skip_fetch,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
