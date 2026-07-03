#!/usr/bin/env python3
"""Materialize cross-sectional relative-strength v0 execution infrastructure v1.

Bounded infrastructure completion: bound-period panel materialization, source manifests,
full evaluation entrypoint dry-run validation. No economic evaluation execution.
Operator GO: GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_INFRASTRUCTURE_COMPLETION_V1
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
from src.research.cross_sectional_bound_period_panel_source_materialization_v1 import (  # noqa: E402
    BoundPeriodSourceMaterializationStatus,
    bound_period_source_result_to_dict,
    materialize_bound_period_panel_from_raw_sources_v1,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (  # noqa: E402
    materialize_panel_staging_source_manifests_v1,
    source_manifest_result_to_dict,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    MaterializationTerminalStatus,
    materialization_result_to_dict,
    materialize_bound_panel_dataset_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    materialize_infrastructure_summary_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_execution_start_state_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (  # noqa: E402
    load_panel_series_from_staging,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
DEFAULT_SOURCE_STAGING = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v1"
)
DEFAULT_BOUND_OUTPUT_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)
PRIOR_BLOCKER_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "economic_evaluation/"
    "bounded_cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v1_"
    "20260703T070255Z"
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
    source_staging_root: Path | None = None,
    bound_output_staging_root: Path | None = None,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / f"bounded_cross_sectional_relative_strength_v0_offline_economic_evaluation_infrastructure_completion_v1_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    ratification = materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        origin_main_sha=origin_main,
    )
    period_binding = ratification["period_binding"]

    source_root = source_staging_root or DEFAULT_SOURCE_STAGING
    output_root = bound_output_staging_root or (durable_evidence_root / DEFAULT_BOUND_OUTPUT_REL)
    source_materialization = materialize_bound_period_panel_from_raw_sources_v1(
        source_root,
        output_root,
        period_binding=period_binding,
    )

    active_staging = output_root
    if source_materialization.status is not BoundPeriodSourceMaterializationStatus.MATERIALIZED:
        active_staging = source_root

    manifest_result = materialize_panel_staging_source_manifests_v1(active_staging)
    materialization = materialize_bound_panel_dataset_v0(
        active_staging,
        period_binding=period_binding,
    )

    entrypoint_payload: dict[str, Any] | None = None
    if materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        panel_series, _ = load_panel_series_from_staging(active_staging)
        entrypoint = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=_REPO_ROOT,
            ratification=ratification,
            staging_root=active_staging,
            panel_series=panel_series,
            go_token=confirm,
        )
        entrypoint_payload = entrypoint_result_to_dict(entrypoint)

    from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
        InfrastructureReadinessResultV0,
        InfrastructureTerminalStatus,
    )

    if materialization.status.value == "DATASET_MATERIALIZATION_COMPLETE":
        readiness = InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE,
            execution_infrastructure_complete=True,
            panel_wiring_complete=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=materialization.panel_data_digest,
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
        f"PRIOR_BLOCKER_EVIDENCE={PRIOR_BLOCKER_EVIDENCE}\n",
        encoding="utf-8",
    )
    (bundle_dir / "SOURCE_MATERIALIZATION_RESULT.json").write_text(
        json.dumps(
            bound_period_source_result_to_dict(source_materialization), indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SOURCE_MANIFEST_RESULT.json").write_text(
        json.dumps(source_manifest_result_to_dict(manifest_result), indent=2, sort_keys=True)
        + "\n",
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

    verdict = "INFRASTRUCTURE_COMPLETION_PASS"
    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        verdict = "INFRASTRUCTURE_COMPLETION_FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"

    return {
        "verdict": verdict,
        "bundle_dir": str(bundle_dir),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_msg": manifest_msg,
        "start_state_valid": start_state.valid,
        "source_materialization_status": source_materialization.status.value,
        "materialization_status": materialization.status.value,
        "infrastructure_status": readiness.status.value,
        "entrypoint_status": entrypoint_payload.get("status") if entrypoint_payload else "NOT_RUN",
        "panel_data_digest": materialization.panel_data_digest,
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
    parser.add_argument("--source-staging-root", type=Path, default=None)
    parser.add_argument("--bound-output-staging-root", type=Path, default=None)
    args = parser.parse_args()
    result = run_materialization(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        source_staging_root=args.source_staging_root,
        bound_output_staging_root=args.bound_output_staging_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
