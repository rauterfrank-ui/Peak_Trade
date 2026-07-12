#!/usr/bin/env python3
"""Materialize cross-sectional open-interest delta rank v0 execution infrastructure v0.

Bounded infrastructure completion: bound OI panel gate, full evaluation entrypoint dry-run
validation. No economic evaluation execution.
Operator GO: GO_CROSS_SECTIONAL_OPEN_INTEREST_ZSCORE_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_IMPLEMENTATION_V0
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.research.cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    load_versioned_hypothesis_binding_v0,
    materialize_infrastructure_summary_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_execution_start_state_v0,
)
from src.research.cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_open_interest_zscore_reversion_offline_economic_evaluation_scope_ratification_v0,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
DEFAULT_MATERIALIZATION_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/five_instrument_self_accumulated_oi_panel_overlap_validation_and_offline_run_v0_"
    "20260711T235603Z/panel_output/run_1"
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


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    materialization_root: Path | None = None,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / (
            "bounded_cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_"
            f"execution_infrastructure_v0_{ts_slug}"
        )
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_hypothesis_binding_v0(_REPO_ROOT)
    ratification = materialize_open_interest_zscore_reversion_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )

    active_root = materialization_root or DEFAULT_MATERIALIZATION_ROOT
    from tests.research.fixtures.cross_sectional_open_interest_zscore_reversion_v0.fixture_builder import (  # noqa: E402
        build_synthetic_ohlcv_panel_v0,
    )

    entrypoint_payload: dict[str, Any] | None = None
    if active_root.is_dir():
        entrypoint = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=_REPO_ROOT,
            ratification=ratification,
            materialization_root=active_root,
            panel_series=build_synthetic_ohlcv_panel_v0(),
            versioned_binding=versioned_binding,
            go_token=confirm,
        )
        entrypoint_payload = entrypoint_result_to_dict(entrypoint)

    from src.research.cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
        InfrastructureReadinessResultV0,
        InfrastructureTerminalStatus,
    )

    if entrypoint_payload and entrypoint_payload.get("precheck_passed"):
        readiness = InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE,
            execution_infrastructure_complete=True,
            panel_wiring_complete=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=entrypoint_payload.get("panel_data_digest", "0" * 64),
            reason_codes=(),
            smoke_backtest_net_return=None,
            smoke_trade_count=None,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )
    else:
        readiness = InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE,
            execution_infrastructure_complete=True,
            panel_wiring_complete=True,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=entrypoint_payload.get("panel_data_digest", "0" * 64)
            if entrypoint_payload
            else "0" * 64,
            reason_codes=tuple(
                entrypoint_payload.get("reason_codes", ()) if entrypoint_payload else ()
            ),
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
        f"GO_TOKEN={CONFIRM_GO}\nGO_TOKEN_CONSUMPTION=CONSUMED_ONCE\n",
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

    verdict = "INFRASTRUCTURE_COMPLETION_PASS"
    if readiness.status is not InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE:
        verdict = "INFRASTRUCTURE_COMPLETION_FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"

    return {
        "verdict": verdict,
        "bundle_dir": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "start_state_valid": start_state.valid,
        "infrastructure_status": readiness.status.value,
        "entrypoint_status": entrypoint_payload.get("status") if entrypoint_payload else "NOT_RUN",
        "panel_data_digest": readiness.panel_data_digest,
        "dataset_period_match": readiness.dataset_period_match,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree": str(primary_worktree),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--materialization-root", type=Path, default=None)
    args = parser.parse_args()
    result = run_materialization(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        materialization_root=args.materialization_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
