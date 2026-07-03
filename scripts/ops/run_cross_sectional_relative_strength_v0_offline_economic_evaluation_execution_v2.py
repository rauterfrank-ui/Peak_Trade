#!/usr/bin/env python3
"""Run cross-sectional relative-strength v0 offline economic evaluation execution v2.

Bounded pipeline: historical source fetch, bound-period materialization, manifest
verification, full six-stage economic evaluation, durable evidence persistence.
Operator GO: GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V2
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

from scripts.ops.fetch_cross_sectional_bound_period_historical_pt1h_sources_v0 import (  # noqa: E402
    BOUND_PERIOD_END_UTC,
    BOUND_WARMUP_START_UTC,
    run_historical_fetch,
)
from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.research.cross_sectional_bound_period_panel_source_materialization_v1 import (  # noqa: E402
    BoundPeriodSourceMaterializationStatus,
    bound_period_source_result_to_dict,
    materialize_bound_period_panel_from_raw_sources_v1,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (  # noqa: E402
    materialize_panel_staging_source_manifests_v1,
    source_manifest_result_to_dict,
    verify_panel_staging_source_manifests_v1,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    MaterializationTerminalStatus,
    materialization_result_to_dict,
    materialize_bound_panel_dataset_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v2 import (  # noqa: E402
    AUTHORITY_EFFECT,
    EXECUTION_VERSION,
    FIXTURE_DATA_DIGEST,
    GO_TOKEN,
    RUNTIME_EFFECT,
    execution_v2_result_to_dict,
    run_full_offline_economic_evaluation_v2,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (  # noqa: E402
    load_panel_series_from_staging,
)

CONFIRM_GO = GO_TOKEN
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_HISTORICAL_SOURCE_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1/v1"
)
DEFAULT_BOUND_OUTPUT_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
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
    dirty_lines = [line for line in dirty.stdout.splitlines() if line.strip()]
    return {
        "head": head.stdout.strip() if head.returncode == 0 else "",
        "dirty_count": len(dirty_lines),
        "dirty_files": dirty_lines,
    }


def run_execution_v2(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    skip_fetch: bool = False,
    historical_source_root: Path | None = None,
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
        / f"bounded_cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v2_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    prechecks = {
        "origin_main": origin_main,
        "expected_origin_main": "84fbdc4e46f6aedafcdf6a445fb16bd5eb0c7f1c",
        "origin_main_match": origin_main == "84fbdc4e46f6aedafcdf6a445fb16bd5eb0c7f1c",
        "primary_worktree_head": primary_before["head"],
        "primary_worktree_dirty_count": primary_before["dirty_count"],
        "primary_worktree_dirty_files": primary_before["dirty_files"],
        "go_token": confirm,
        "fixture_data_digest": FIXTURE_DATA_DIGEST,
        "bound_period_start": "2024-05-30T20:00:00Z",
        "bound_period_end": BOUND_PERIOD_END_UTC,
    }
    (bundle_dir / "PRECHECKS.json").write_text(
        json.dumps(prechecks, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not prechecks["origin_main_match"]:
        _die("ERR: origin_main_mismatch_fail_closed")

    ratification = materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
    )
    period_binding = ratification["period_binding"]

    historical_root = historical_source_root or (
        durable_evidence_root / DEFAULT_HISTORICAL_SOURCE_REL
    )
    bound_output = bound_output_staging_root or (durable_evidence_root / DEFAULT_BOUND_OUTPUT_REL)

    fetch_result: dict[str, Any] | None = None
    if not skip_fetch:
        fetch_result = run_historical_fetch(
            confirm=confirm,
            target_staging_root=historical_root,
            durable_evidence_root=durable_evidence_root,
            period_start_utc=BOUND_WARMUP_START_UTC,
            period_end_utc=BOUND_PERIOD_END_UTC,
        )

    source_materialization = materialize_bound_period_panel_from_raw_sources_v1(
        historical_root,
        bound_output,
        period_binding=period_binding,
    )
    if skip_fetch and bound_output.is_dir():
        active_staging = bound_output
    elif source_materialization.status is BoundPeriodSourceMaterializationStatus.MATERIALIZED:
        active_staging = bound_output
    else:
        active_staging = historical_root

    manifest_result = materialize_panel_staging_source_manifests_v1(active_staging)
    manifest_ok, manifest_rc, manifest_reasons = verify_panel_staging_source_manifests_v1(
        active_staging
    )

    materialization_a = materialize_bound_panel_dataset_v0(
        active_staging,
        period_binding=period_binding,
    )
    materialization_b = materialize_bound_panel_dataset_v0(
        active_staging,
        period_binding=period_binding,
    )
    rematerialization_match = (
        materialization_a.panel_data_digest == materialization_b.panel_data_digest
        and materialization_a.status == materialization_b.status
    )

    evaluation_payload: dict[str, Any] | None = None
    if materialization_a.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        panel_series, _ = load_panel_series_from_staging(active_staging)
        evaluation = run_full_offline_economic_evaluation_v2(
            repo_root=_REPO_ROOT,
            ratification=ratification,
            staging_root=active_staging,
            panel_series=panel_series,
            go_token=confirm,
        )
        evaluation_payload = execution_v2_result_to_dict(evaluation)
        (bundle_dir / "ECONOMIC_VIABILITY_EVIDENCE_V1.json").write_text(
            json.dumps(evaluation.economic_viability_evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    payload: dict[str, Any] = {
        "verdict": (
            evaluation_payload["status"] if evaluation_payload else "FAIL_CLOSED_DATASET_GATE"
        ),
        "process_classification": "BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V2",
        "go_token": confirm,
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "historical_source_root": str(historical_root),
        "bound_output_staging_root": str(bound_output),
        "active_staging_root": str(active_staging),
        "fetch_result": fetch_result,
        "source_materialization": bound_period_source_result_to_dict(source_materialization),
        "source_manifests": source_manifest_result_to_dict(manifest_result),
        "manifest_verify_rc": manifest_rc,
        "manifest_verify_reasons": list(manifest_reasons),
        "dataset_materialization": materialization_result_to_dict(materialization_a),
        "deterministic_rematerialization_status": "PASS" if rematerialization_match else "FAIL",
        "rematerialization_digest_a": materialization_a.panel_data_digest,
        "rematerialization_digest_b": materialization_b.panel_data_digest,
        "evaluation": evaluation_payload,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "durable_evidence_path": str(bundle_dir),
    }
    (bundle_dir / "EXECUTION_V2_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    rc, verify_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload["manifest_verify_rc"] = rc
    payload["manifest_verify_msg"] = verify_msg
    (bundle_dir / "EXECUTION_V2_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    retention.finalize_durable_bundle_manifest(bundle_dir)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, default=_REPO_ROOT)
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--historical-source-root", type=Path, default=None)
    parser.add_argument("--bound-output-staging-root", type=Path, default=None)
    args = parser.parse_args()
    result = run_execution_v2(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        skip_fetch=args.skip_fetch,
        historical_source_root=args.historical_source_root,
        bound_output_staging_root=args.bound_output_staging_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
