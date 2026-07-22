"""Executable development-evaluation path for VCEB v1 (orchestration surface).

Authorization is fail-closed. Dry-validate never starts the runner, opens a panel,
or consumes run budget. Real evaluate requires repo authorization flags + token;
unauthorized calls terminate before any dataset access.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.authorization_v1 import (
    AuthorizationDecisionV1,
    resolve_authorization_decision_v1,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.binding_v1 import (
    assert_shared_channel_core_bound,
    compute_config_digest,
    compute_strategy_params_digest,
    resolve_cost_execution_binding,
    resolve_measurement_contract,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEVELOPMENT_RUN_LIMIT,
    TIME_SEGMENT_DEFINITION_ID,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.evidence_schema_v1 import (
    empty_evidence_surface_template,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_run_counters_unchanged,
    preflight_guards,
    read_run_counters,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.time_segments_v1 import (
    partition_chronological_equal_duration_quarters_v1,
    segments_to_dict,
)


@dataclass(frozen=True)
class EvaluatePathResultV1:
    status: str
    mode: str
    runner_started: bool
    evaluation_executed: bool
    holdout_accessed: bool
    development_dataset_loaded: bool
    authorization: dict[str, Any]
    run_counters: dict[str, int]
    evidence_surface: dict[str, Any] | None
    executable_path_reached: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "runner_started": self.runner_started,
            "evaluation_executed": self.evaluation_executed,
            "holdout_accessed": self.holdout_accessed,
            "development_dataset_loaded": self.development_dataset_loaded,
            "authorization": self.authorization,
            "run_counters": self.run_counters,
            "evidence_surface": self.evidence_surface,
            "executable_path_reached": self.executable_path_reached,
            "reason": self.reason,
            "development_run_limit": DEVELOPMENT_RUN_LIMIT,
            "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
            "dataset_id": DATASET_ID,
        }


def _auth_dict(decision: AuthorizationDecisionV1) -> dict[str, Any]:
    return {
        "authorized": decision.authorized,
        "authorize_token_valid": decision.authorize_token_valid,
        "repo_development_evaluation_authorized": decision.repo_development_evaluation_authorized,
        "program_development_evaluation_authorized": (
            decision.program_development_evaluation_authorized
        ),
        "entry_point_binding_authorized": decision.entry_point_binding_authorized,
        "reason_codes": list(decision.reason_codes),
    }


def dry_validate_evaluate_path_v1(repo_root: Path) -> EvaluatePathResultV1:
    """Validate executable path contracts without runner start or counter mutation."""
    before = read_run_counters(repo_root)
    guards = preflight_guards(repo_root)
    contract = resolve_measurement_contract(repo_root)
    assert_shared_channel_core_bound()
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest(contract)
    segments = segments_to_dict(partition_chronological_equal_duration_quarters_v1())
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
            for s in segments
        ],
    )
    after = read_run_counters(repo_root)
    assert_run_counters_unchanged(before, after)
    return EvaluatePathResultV1(
        status="DRY_VALIDATE_PASS_EVALUATION_UNAUTHORIZED",
        mode="dry-validate",
        runner_started=False,
        evaluation_executed=False,
        holdout_accessed=False,
        development_dataset_loaded=False,
        authorization={
            "authorized": False,
            "guards": guards,
            "cost_execution_binding": resolve_cost_execution_binding(contract),
        },
        run_counters=after,
        evidence_surface=evidence,
        executable_path_reached=True,
        reason="DEVELOPMENT_EVALUATION_UNAUTHORIZED_ON_HEAD",
    )


def run_authorized_development_evaluation_v1(
    repo_root: Path,
    *,
    authorize_token: str,
    output_dir: Path | None = None,
    persist_evidence: bool = False,
) -> EvaluatePathResultV1:
    """Evaluate path: fail-closed without authorization; never opens dataset when denied."""
    del output_dir, persist_evidence  # unused while unauthorized; no evidence write
    before = read_run_counters(repo_root)
    decision = resolve_authorization_decision_v1(repo_root, authorize_token=authorize_token)
    after = read_run_counters(repo_root)
    assert_run_counters_unchanged(before, after)
    if not decision.authorized:
        return EvaluatePathResultV1(
            status="FAIL_CLOSED",
            mode="evaluate",
            runner_started=False,
            evaluation_executed=False,
            holdout_accessed=False,
            development_dataset_loaded=False,
            authorization=_auth_dict(decision),
            run_counters=after,
            evidence_surface=None,
            executable_path_reached=False,
            reason="EVALUATION_UNAUTHORIZED:" + ",".join(decision.reason_codes or ("UNKNOWN",)),
        )
    # Authorized path is reserved for a later separate operator GO / wiring slice.
    # This entry-point-only surface must not open the development panel.
    raise GuardError("AUTHORIZED_PANEL_EXECUTION_BOUNDARY_NOT_MATERIALIZED_IN_THIS_SLICE")
