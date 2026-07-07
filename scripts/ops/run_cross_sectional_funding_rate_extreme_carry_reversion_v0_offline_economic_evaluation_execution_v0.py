#!/usr/bin/env python3
"""Offline economic evaluation runner for cross-sectional funding-rate extreme-carry-reversion v0.

Supports infrastructure dry-run (readiness + entrypoint wiring validation) and
full offline economic evaluation execution paths. Operator GO tokens:

- Infrastructure dry-run:
  GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_INFRASTRUCTURE_COMPLETION_V0
- Full execution:
  GO_CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_NO_RUNTIME_AUTHORITY_V0
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
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    MaterializationTerminalStatus,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    COMBINED_RATIFY_AND_EXECUTE_GO_TOKEN,
    EXECUTION_VERSION,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    execution_result_to_dict,
    load_ohlcv_panel_series_for_backtest,
    load_versioned_research_binding_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_full_offline_economic_evaluation_v0,
    verify_execution_start_state_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_infrastructure_readiness_v0 import (  # noqa: E402
    evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0,
    readiness_result_to_dict,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_extreme_carry_reversion_offline_economic_evaluation_scope_ratification_v0,
)

INFRASTRUCTURE_CONFIRM_GOS = frozenset(
    {INFRASTRUCTURE_GO_TOKEN, COMBINED_RATIFY_AND_EXECUTE_GO_TOKEN}
)
EXECUTION_CONFIRM_GOS = frozenset({GO_TOKEN, COMBINED_RATIFY_AND_EXECUTE_GO_TOKEN})
MAX_RUNTIME_SECONDS = 1500
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SCOPE_CLASSIFICATION = "BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"


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


def run_infrastructure_dry_run_v0(
    *,
    staging_root: Path,
    output_json: Path | None = None,
) -> dict[str, Any]:
    ratification = (
        materialize_extreme_carry_reversion_offline_economic_evaluation_scope_ratification_v0(
            repo_root=_REPO_ROOT,
        )
    )
    readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
    )
    if not readiness.evaluation_infrastructure_ready:
        _die(f"ERR:infrastructure_not_ready:{readiness.blockers}")

    try:
        panel_series = load_ohlcv_panel_series_for_backtest(staging_root)
    except FileNotFoundError:
        _die("ERR:staging_root_missing_ohlcv_panel")

    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=staging_root,
        panel_series=panel_series,
        confirm_go=INFRASTRUCTURE_GO_TOKEN,
    )
    payload = {
        "execution_mode": "INFRASTRUCTURE_DRY_RUN",
        "readiness": readiness_result_to_dict(readiness),
        "entrypoint": entrypoint_result_to_dict(result),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "economic_evaluation_executed": False,
        "promotion_granted": False,
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_json:
        output_json.write_text(text, encoding="utf-8")
    return payload


def run_offline_economic_evaluation_execution_v0(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    start_monotonic = time.monotonic()
    if confirm not in EXECUTION_CONFIRM_GOS:
        _die(f"ERR:confirm_go_token_required:{'|'.join(sorted(EXECUTION_CONFIRM_GOS))}")

    origin_main = _resolve_origin_main(_REPO_ROOT)
    primary_before = _primary_worktree_snapshot(primary_worktree)
    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = (
        durable_evidence_root
        / "implementation"
        / f"bounded_cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_execution_v0_{ts_slug}"
    )
    bundle_dir.mkdir(parents=True, exist_ok=False)

    versioned_binding = load_versioned_research_binding_v0(_REPO_ROOT)
    ratification = (
        materialize_extreme_carry_reversion_offline_economic_evaluation_scope_ratification_v0(
            repo_root=_REPO_ROOT,
            versioned_binding=versioned_binding,
        )
    )
    start_state = verify_execution_start_state_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        versioned_binding=versioned_binding,
        origin_main_sha=origin_main,
    )
    _guard_timeout(start_monotonic)

    materialization = materialize_bound_funding_panel_dataset_v0(
        staging_root,
        period_binding=versioned_binding["period_binding"],
        expected_data_digest=versioned_binding["data_digest"],
    )
    _guard_timeout(start_monotonic)

    evaluation_payload: dict[str, Any] | None = None
    evaluation = None
    if materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        panel_series = load_ohlcv_panel_series_for_backtest(staging_root)
        evaluation = run_full_offline_economic_evaluation_v0(
            repo_root=_REPO_ROOT,
            ratification=ratification,
            staging_root=staging_root,
            panel_series=panel_series,
            versioned_binding=versioned_binding,
            confirm_go=confirm,
        )
        evaluation_payload = execution_result_to_dict(evaluation)
        if evaluation.economic_viability_evidence:
            (bundle_dir / "ECONOMIC_VIABILITY_EVIDENCE_V1.json").write_text(
                json.dumps(evaluation.economic_viability_evidence, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    _guard_timeout(start_monotonic)

    economic_executed = evaluation.economic_evaluation_executed if evaluation is not None else False
    economic_classification = (
        evaluation.economic_classification.value if evaluation is not None else "FAIL_CLOSED"
    )
    (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").write_text(
        f"ECONOMIC_EVALUATION_EXECUTED={'true' if economic_executed else 'false'}\n",
        encoding="utf-8",
    )

    primary_after = _primary_worktree_snapshot(primary_worktree)
    worktree_protected = (
        primary_before["head"] == primary_after["head"]
        and primary_before["dirty_count"] == primary_after["dirty_count"]
    )

    payload: dict[str, Any] = {
        "verdict": (
            evaluation_payload["status"] if evaluation_payload else "FAIL_CLOSED_DATASET_GATE"
        ),
        "process_classification": SCOPE_CLASSIFICATION,
        "execution_mode": "FULL_OFFLINE_ECONOMIC_EVALUATION",
        "execution_version": EXECUTION_VERSION,
        "origin_main": origin_main,
        "staging_root": str(staging_root),
        "start_state_valid": start_state.valid,
        "evaluation": evaluation_payload,
        "economic_classification": economic_classification,
        "economic_evaluation_executed": economic_executed,
        "promotion_granted": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "primary_worktree_protected": worktree_protected,
        "durable_evidence_path": str(bundle_dir),
        "elapsed_seconds": round(time.monotonic() - start_monotonic, 3),
        "timeout_guard_seconds": MAX_RUNTIME_SECONDS,
    }
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SCOPE_AND_GO.txt").write_text(
        "\n".join(
            [
                "EXECUTION_SCOPE=FULL_OFFLINE_ECONOMIC_EVALUATION_V0",
                f"GO_TOKEN={confirm}",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "SAFETY_INVARIANTS.env").write_text(
        "\n".join(
            [
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                "NO_LIVE_ACTIONS=true",
                "NO_CREDENTIALS=true",
                "PROMOTION_GRANTED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(bundle_dir)
    payload["manifest_verify_rc"] = manifest_rc
    payload["manifest_verify_msg"] = manifest_msg
    (bundle_dir / "EXECUTION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _guard_timeout(start_monotonic)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go-token", default=None)
    parser.add_argument("--confirm", default=None)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, default=None)
    args = parser.parse_args()

    confirm = args.confirm or args.confirm_go_token
    if confirm is None:
        _die("ERR:confirm_go_token_required")

    if confirm in EXECUTION_CONFIRM_GOS:
        if args.primary_worktree is None:
            _die("ERR:primary_worktree_required_for_full_execution")
        payload = run_offline_economic_evaluation_execution_v0(
            confirm=confirm,
            durable_evidence_root=args.durable_evidence_root,
            primary_worktree=args.primary_worktree,
            staging_root=args.staging_root,
        )
    elif confirm in INFRASTRUCTURE_CONFIRM_GOS:
        payload = run_infrastructure_dry_run_v0(
            staging_root=args.staging_root,
            output_json=args.output_json,
        )
    else:
        _die(
            "ERR:invalid_go_token:"
            f"expected_one_of:{'|'.join(sorted(INFRASTRUCTURE_CONFIRM_GOS | EXECUTION_CONFIRM_GOS))}"
        )

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output_json and confirm not in INFRASTRUCTURE_CONFIRM_GOS:
        args.output_json.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
