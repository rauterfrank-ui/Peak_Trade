"""Development-evaluation entry point for VOLATILITY_DECAY_BREAKOUT_V1.

Preflight and dry-validate never start a runner, open a dataset, or consume run budget.
Evaluate requires machine-checkable authorization; unauthorized calls fail closed
before any panel access.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.research.volatility_decay_breakout_v1_development_evaluation_v1.binding_v1 import (
    assert_shared_channel_core_bound,
    compute_config_digest,
    compute_strategy_params_digest,
    load_and_validate_entry_point_binding,
    materialize_entry_point_binding_payload,
    resolve_cost_execution_binding,
    resolve_measurement_contract,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.constants_v1 import (
    BASELINE_ID,
    CLI_REL_PATH,
    DATASET_ID,
    EVIDENCE_REL_PATH,
    OWNER_SURFACE,
    PACKAGE_MARKER,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.evaluate_path_v1 import (
    dry_validate_evaluate_path_v1,
    run_authorized_development_evaluation_v1,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.evidence_schema_v1 import (
    empty_evidence_surface_template,
    validate_evidence_surface_complete,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    preflight_guards,
    read_run_counters,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.time_segments_v1 import (
    partition_chronological_equal_duration_quarters_v1,
    segments_to_dict,
)


def run_preflight_only(repo_root: Path, *, output_dir: Path | None = None) -> dict[str, Any]:
    """Static preflight: bind digests, segments, guards, evidence schema. No panel open."""
    guard_report = preflight_guards(repo_root)
    assert_shared_channel_core_bound()
    binding = materialize_entry_point_binding_payload(repo_root)
    contract = resolve_measurement_contract(repo_root)
    segments = partition_chronological_equal_duration_quarters_v1()
    segment_dicts = segments_to_dict(segments)
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest(contract)
    evidence = empty_evidence_surface_template(
        config_digest=config_digest,
        strategy_params_digest=strategy_params_digest,
        dataset_id=DATASET_ID,
        segment_boundaries=[
            {
                "segment_id": s["segment_id"],
                "range": s["range"],
                "evaluable_treatment_breakout_events": "NOT_EXECUTED",
                "result": "NOT_EXECUTED",
                "bar_count": s["bar_count"],
            }
            for s in segment_dicts
        ],
    )
    validate_evidence_surface_complete(evidence)
    cost_binding = resolve_cost_execution_binding(contract)
    report = {
        "package_marker": PACKAGE_MARKER,
        "owner_surface": OWNER_SURFACE,
        "mode": "preflight",
        "runner_started": False,
        "evaluation_executed": False,
        "holdout_accessed": False,
        "development_dataset_loaded": False,
        "development_evaluation_authorized": False,
        "dataset_id": DATASET_ID,
        "baseline_id": BASELINE_ID,
        "config_digest": config_digest,
        "strategy_params_digest": strategy_params_digest,
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
        "time_segments": segment_dicts,
        "cost_execution_binding": cost_binding,
        "entry_point_binding": binding,
        "guards": guard_report,
        "evidence_surface": evidence,
        "cli_ref": CLI_REL_PATH,
        "evidence_ref": EVIDENCE_REL_PATH,
        "run_counters": read_run_counters(repo_root),
        "shared_channel_core_bound": True,
        "executable_evaluate_path_present": True,
        "status": "PREFLIGHT_PASS_EVALUATION_UNAUTHORIZED",
        "verdict": (
            "EXECUTABLE_EVALUATE_PATH_PRESENT_AWAITING_SEPARATE_OPERATOR_GO_"
            "FOR_DEVELOPMENT_EVALUATION_AUTHORIZATION"
        ),
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "preflight_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return report


def run_dry_validate(repo_root: Path) -> dict[str, Any]:
    return dry_validate_evaluate_path_v1(repo_root).to_dict()


def run_evaluate_fail_closed(
    repo_root: Path,
    *,
    authorize_token: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Evaluate path: fail-closed without authorization; never starts runner when denied."""
    result = run_authorized_development_evaluation_v1(
        repo_root,
        authorize_token=authorize_token,
        output_dir=output_dir,
        persist_evidence=True,
    )
    if not result.authorization.get("authorized"):
        raise GuardError(result.reason or "EVALUATION_UNAUTHORIZED")
    return result.to_dict()


def validate_repo_entry_point(repo_root: Path) -> dict[str, Any]:
    binding = load_and_validate_entry_point_binding(repo_root)
    preflight = run_preflight_only(repo_root)
    dry = dry_validate_evaluate_path_v1(repo_root)
    return {
        "valid": True,
        "binding_status": binding["status"],
        "preflight_status": preflight["status"],
        "dry_validate_status": dry.status,
        "executable_evaluate_path_present": True,
        "runner_started": False,
        "evaluation_executed": False,
        "development_evaluation_authorized": False,
        "run_counters": preflight["run_counters"],
    }
