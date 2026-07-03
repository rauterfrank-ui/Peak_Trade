#!/usr/bin/env python3
"""Infrastructure-only runner for funding-rate delta momentum v0 (no economic evaluation)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    MaterializationTerminalStatus,
    materialization_result_to_dict,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    INFRASTRUCTURE_GO_TOKEN,
    InfrastructureReadinessResultV0,
    InfrastructureTerminalStatus,
    entrypoint_result_to_dict,
    load_versioned_research_binding_v0,
    materialize_infrastructure_summary_v0,
    run_full_evaluation_entrypoint_dry_run_v0,
    verify_execution_start_state_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_funding_delta_momentum_offline_evaluation_scope_ratification_v0,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/extended_chronological_v1"
)
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def _resolve_origin_main(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, default=Path("/Users/frnkhrz/Peak_Trade"))
    args = parser.parse_args()
    if args.confirm != CONFIRM_GO:
        print(f"ERR: confirm_go_token_required:{CONFIRM_GO}", file=sys.stderr)
        raise SystemExit(2)

    origin_main = _resolve_origin_main(_REPO_ROOT)
    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
    ratification = materialize_funding_delta_momentum_offline_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    materialization = materialize_bound_funding_panel_dataset_v0(
        args.staging_root,
        period_binding=versioned_binding["period_binding"],
        expected_data_digest=versioned_binding["data_digest"],
    )
    entrypoint = run_full_evaluation_entrypoint_dry_run_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=args.staging_root,
        versioned_binding=versioned_binding,
        go_token=args.confirm,
    )
    readiness = InfrastructureReadinessResultV0(
        status=(
            InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE
            if materialization.status
            is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
            and entrypoint.precheck_passed
            else InfrastructureTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE
        ),
        execution_infrastructure_complete=entrypoint.stage_wiring_complete,
        panel_wiring_complete=entrypoint.stage_wiring_complete,
        bound_dataset_materialized=(
            materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        ),
        dataset_period_match=(
            materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        ),
        panel_data_digest=materialization.panel_data_digest,
        reason_codes=materialization.reason_codes + entrypoint.fail_reasons,
        authority_effect="NONE",
        runtime_effect="NONE",
        economic_evaluation_executed=False,
    )
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        args.durable_evidence_root
        / "implementation"
        / f"bounded_cross_sectional_funding_rate_delta_momentum_v0_panel_and_implementation_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)
    summary = materialize_infrastructure_summary_v0(
        ratification=ratification,
        readiness=readiness,
        origin_main_sha=origin_main,
        execution_bundle_dir=str(bundle_dir),
    )
    (bundle_dir / "START_STATE.json").write_text(
        json.dumps(
            {
                "valid": start_state.valid,
                "fail_reasons": list(start_state.fail_reasons),
                "origin_main_sha": start_state.origin_main_sha,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "DATASET_MATERIALIZATION_RESULT.json").write_text(
        json.dumps(materialization_result_to_dict(materialization), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "ENTRYPOINT_DRY_RUN_RESULT.json").write_text(
        json.dumps(entrypoint_result_to_dict(entrypoint), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "INFRASTRUCTURE_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "verdict": readiness.status.value,
                "economic_evaluation_executed": False,
                "bundle_dir": str(bundle_dir),
                "start_state_valid": start_state.valid,
                "entrypoint_status": entrypoint.status,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
