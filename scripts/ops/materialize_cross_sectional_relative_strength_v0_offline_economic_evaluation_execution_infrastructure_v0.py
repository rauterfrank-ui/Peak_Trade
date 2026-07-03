#!/usr/bin/env python3
"""Materialize cross-sectional relative-strength v0 execution infrastructure v0.

Bounded infrastructure completion for offline economic evaluation execution path.
Does not execute full economic evaluation or emit PASS/FAIL/INCONCLUSIVE verdicts.
Operator GO: GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_COMPLETION_V0
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

from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    materialization_result_to_dict,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    materialize_infrastructure_summary_v0,
    verify_execution_start_state_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    panel_staging_root: Path | None = None,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / f"bounded_cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_infrastructure_completion_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    ratification = materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
    )

    from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
        materialize_bound_panel_dataset_v0,
    )

    period_binding = ratification["period_binding"]
    staging = panel_staging_root or Path(
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v1"
    )
    materialization = materialize_bound_panel_dataset_v0(staging, period_binding=period_binding)

    (bundle_dir / "START_HEAD.txt").write_text(
        subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout,
        encoding="utf-8",
    )
    (bundle_dir / "ORIGIN_MAIN.txt").write_text(origin_main + "\n", encoding="utf-8")
    (bundle_dir / "SCOPE_AND_GO.txt").write_text(
        f"GO_TOKEN={CONFIRM_GO}\nPROCESS=INFRASTRUCTURE_COMPLETION\n",
        encoding="utf-8",
    )
    (bundle_dir / "BINDING_VALIDATION.txt").write_text(
        f"START_STATE_VALID={start_state.valid}\nFAIL_REASONS={start_state.fail_reasons}\n",
        encoding="utf-8",
    )
    (bundle_dir / "VERSIONED_CONFIG.json").write_text(
        json.dumps(
            json.loads(
                (
                    _REPO_ROOT
                    / "config/ops/cross_sectional_relative_strength_v0_economic_evaluation_v1.json"
                ).read_text(encoding="utf-8")
            ),
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
    (bundle_dir / "DATA_DIGEST.txt").write_text(
        f"PANEL_DATA_DIGEST={materialization.panel_data_digest}\nSTATUS={materialization.status.value}\n",
        encoding="utf-8",
    )

    from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
        InfrastructureTerminalStatus,
        InfrastructureReadinessResultV0,
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
    (bundle_dir / "INFRASTRUCTURE_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "bundle_dir": str(bundle_dir),
        "start_state_valid": start_state.valid,
        "materialization_status": materialization.status.value,
        "infrastructure_status": readiness.status.value,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree": str(primary_worktree),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--panel-staging-root", type=Path, default=None)
    args = parser.parse_args()
    result = run_materialization(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        panel_staging_root=args.panel_staging_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
