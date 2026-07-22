"""Development-evaluation entry point for CS RS momentum v1 (preflight-only by default).

Evaluate mode remains fail-closed while development_evaluation_authorized=false.
No runner start / run-slot consumption in the infrastructure slice.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.binding_v1 import (
    compute_config_digest,
    compute_strategy_params_digest,
    load_and_validate_entry_point_binding,
    materialize_entry_point_binding_payload,
    resolve_cost_execution_binding,
    resolve_measurement_contract,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.constants_v1 import (
    CLI_REL_PATH,
    DATASET_ID,
    EVIDENCE_REL_PATH,
    HYPOTHESIS_ID,
    OWNER_SURFACE,
    PACKAGE_MARKER,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.evidence_schema_v1 import (
    empty_evidence_surface_template,
    validate_evidence_surface_complete,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_authorize_token,
    assert_evaluation_unauthorized_for_this_slice,
    assert_no_slot_reuse,
    preflight_guards,
    read_run_counters,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.time_segments_v1 import (
    partition_chronological_equal_duration_quarters_v1,
    segments_to_dict,
)


def run_preflight_only(repo_root: Path, *, output_dir: Path | None = None) -> dict[str, Any]:
    """Static preflight: bind digests, segments, guards, evidence schema. No panel open."""
    guard_report = preflight_guards(repo_root)
    binding = materialize_entry_point_binding_payload(repo_root)
    contract = resolve_measurement_contract(repo_root)
    segments = partition_chronological_equal_duration_quarters_v1()
    segment_dicts = segments_to_dict(segments)
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest()
    evidence = empty_evidence_surface_template(
        config_digest=config_digest,
        strategy_params_digest=strategy_params_digest,
        dataset_id=DATASET_ID,
        segment_boundaries=[
            {
                "segment_id": s["segment_id"],
                "range": s["range"],
                "valid_rebalance_observations": "NOT_EXECUTED",
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
        "dataset_id": DATASET_ID,
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
        "status": "PREFLIGHT_PASS_EVALUATION_UNAUTHORIZED",
        "verdict": "ENTRY_POINT_MATERIALIZED_AWAITING_SEPARATE_OPERATOR_GO_FOR_EVALUATION_EXECUTION",
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "preflight_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return report


def run_evaluate_fail_closed(
    repo_root: Path,
    *,
    authorize_token: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Evaluate path: fail-closed while evaluation remains unauthorized. Never starts a run."""
    assert_authorize_token(authorize_token)
    assert_no_slot_reuse(output_dir)
    assert_evaluation_unauthorized_for_this_slice(repo_root)
    # Explicit fail-closed: infrastructure exists, execution not authorized on HEAD.
    raise GuardError(f"EVALUATION_UNAUTHORIZED_AWAITING_SEPARATE_OPERATOR_GO:{HYPOTHESIS_ID}")


def validate_repo_entry_point(repo_root: Path) -> dict[str, Any]:
    binding = load_and_validate_entry_point_binding(repo_root)
    preflight = run_preflight_only(repo_root)
    return {
        "valid": True,
        "binding_status": binding["status"],
        "preflight_status": preflight["status"],
        "runner_started": False,
        "evaluation_executed": False,
        "run_counters": preflight["run_counters"],
    }
