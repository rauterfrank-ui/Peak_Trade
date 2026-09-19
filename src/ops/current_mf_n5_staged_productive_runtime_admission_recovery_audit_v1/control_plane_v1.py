"""Staged productive Full-Autonomy N=5 control plane — admission, aggregate, audit."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, NoReturn

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.orchestrator_v1 import (
    ProductiveFullAutonomyCap24BindContextV1,
    ProductiveFullAutonomyN5RuntimeOrchestratorResultV1,
    run_productive_full_autonomy_n5_runtime_orchestrator_v1,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.aggregate_admission_v1 import (
    AggregateMultiLaneAdmissionV1,
    compose_aggregate_multi_lane_admission_v1,
    lane_mv2_dp_provenance_from_readiness,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.audit_v1 import (
    ProductiveN5RuntimeAuditEvidenceV1,
    build_productive_n5_runtime_audit_evidence_v1,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.constants_v1 import (
    ADMISSION_DENIED_N_GT_1,
    AUTONOMY_TRADING_DECISION_AUTHORITY,
    EXTERNAL_EFFECT_AUTHORIZED,
    FAILURE_AUTHORITY,
    FAILURE_EXTERNAL_EFFECT,
    FAILURE_FORBIDDEN_HARNESS,
    FAILURE_TERMINAL,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    N_GT_1_PRODUCTIVE_AUTHORIZATION,
    OWNER,
    POST_ALLOWED,
    SCHEMA_VERSION,
    TERMINAL_BOUNDARY_FAIL_CLOSED,
    TERMINAL_BOUNDARY_PRE_EXTERNAL,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.recovery_classification_v1 import (
    ProductiveRuntimeRecoveryClassificationV1,
    classify_productive_runtime_recovery_v1,
)
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1.staged_cardinality_v1 import (
    StagedTargetCardinalityDecisionV1,
    evaluate_staged_target_cardinality_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_FAIL_CLOSED,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    MembershipContextArtifactV1,
    validate_membership_context_artifact_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)


class StagedProductiveN5RuntimeControlPlaneError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


@dataclass(frozen=True)
class StagedProductiveN5RuntimeControlPlaneResultV1:
    terminal_boundary: str
    cardinality: StagedTargetCardinalityDecisionV1
    aggregate: AggregateMultiLaneAdmissionV1
    recovery: ProductiveRuntimeRecoveryClassificationV1
    audit: ProductiveN5RuntimeAuditEvidenceV1
    orchestrator_result: ProductiveFullAutonomyN5RuntimeOrchestratorResultV1 | None
    external_effect_authorized: bool
    post_allowed: bool


def _fail(code: str, detail: str = "") -> NoReturn:
    raise StagedProductiveN5RuntimeControlPlaneError(code, detail)


def _assert_control_plane_authority() -> None:
    if (
        AUTONOMY_TRADING_DECISION_AUTHORITY
        or N_GT_1_PRODUCTIVE_AUTHORIZATION
        or N_GT_1_ENABLED
        or MULTI_FUTURE_RUNTIME_AUTHORIZED
        or EXTERNAL_EFFECT_AUTHORIZED
        or POST_ALLOWED
        or int(MAX_POSITIONS_EFFECTIVE) != 1
    ):
        _fail(FAILURE_AUTHORITY, OWNER)


def _terminal_from_aggregate(aggregate: AggregateMultiLaneAdmissionV1) -> str:
    if aggregate.aggregate_disposition == DISPOSITION_FAIL_CLOSED:
        return TERMINAL_BOUNDARY_FAIL_CLOSED
    return TERMINAL_BOUNDARY_PRE_EXTERNAL


def run_staged_productive_full_autonomy_n5_runtime_control_plane_v1(
    *,
    membership: MembershipContextArtifactV1,
    ranking_snapshot: Mapping[str, Any],
    topology_state_root_base: Path | str,
    lane_assignment_writer: DurableLaneAssignmentSingleWriterV1,
    cap24_bind: ProductiveFullAutonomyCap24BindContextV1,
    repository_sha: str,
    producer_observed_at_unix: float,
    origin_main_sha: str,
    requested_target_cardinality: int,
    portfolio_budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
    architectural_composition_harness: bool = False,
    **cycle_kwargs: Any,
) -> StagedProductiveN5RuntimeControlPlaneResultV1:
    """Governed productive entry: staged admission → orchestrator → aggregate → audit."""
    _assert_control_plane_authority()
    validate_membership_context_artifact_v1(membership)
    recovery = classify_productive_runtime_recovery_v1(membership=membership)
    cardinality = evaluate_staged_target_cardinality_v1(
        requested_target_cardinality=requested_target_cardinality,
        architectural_composition_harness=architectural_composition_harness,
    )

    owner = (
        portfolio_budget_owner
        if portfolio_budget_owner is not None
        else PortfolioCapitalReservationBudgetOwnerV1()
    )
    orch: ProductiveFullAutonomyN5RuntimeOrchestratorResultV1 | None = None
    lane_rollups = ()
    occupied: tuple[str, ...] = ()
    provenance: tuple[tuple[str, str, str], ...] = ()
    portfolio_admitted = False
    portfolio_active_sum = Decimal("0")

    if cardinality.admission_class == ADMISSION_DENIED_N_GT_1:
        aggregate = compose_aggregate_multi_lane_admission_v1(
            cardinality=cardinality,
            lane_rollups=(),
        )
    else:
        if cardinality.architectural_harness_used and not architectural_composition_harness:
            _fail(FAILURE_FORBIDDEN_HARNESS, "harness_flag_mismatch")
        orch = run_productive_full_autonomy_n5_runtime_orchestrator_v1(
            membership=membership,
            ranking_snapshot=ranking_snapshot,
            topology_state_root_base=topology_state_root_base,
            lane_assignment_writer=lane_assignment_writer,
            cap24_bind=cap24_bind,
            repository_sha=repository_sha,
            producer_observed_at_unix=producer_observed_at_unix,
            origin_main_sha=origin_main_sha,
            target_cardinality=cardinality.invocation_cardinality,
            portfolio_budget_owner=owner,
            **cycle_kwargs,
        )
        if orch.external_effect_authorized or orch.post_allowed:
            _fail(FAILURE_EXTERNAL_EFFECT, OWNER)
        for rollup in orch.lane_rollups:
            if int(rollup.post_count) != 0 or rollup.permit_created:
                _fail(FAILURE_EXTERNAL_EFFECT, rollup.lane_id)
        lane_rollups = orch.lane_rollups
        occupied = orch.occupied_lane_ids
        provenance = lane_mv2_dp_provenance_from_readiness(orch.readiness_projections)
        portfolio_admitted = bool(orch.portfolio_admitted)
        portfolio_active_sum = orch.portfolio_active_sum
        aggregate = compose_aggregate_multi_lane_admission_v1(
            cardinality=cardinality,
            lane_rollups=lane_rollups,
        )
        if aggregate.aggregate_disposition == DISPOSITION_FAIL_CLOSED and orch.terminal_boundary:
            if any(r.disposition == DISPOSITION_FAIL_CLOSED for r in lane_rollups):
                _fail(FAILURE_TERMINAL, "lane_fail_closed")

    terminal = _terminal_from_aggregate(aggregate)
    audit = build_productive_n5_runtime_audit_evidence_v1(
        schema_version=SCHEMA_VERSION,
        membership=membership,
        cardinality=cardinality,
        aggregate=aggregate,
        occupied_lane_ids=occupied,
        per_lane_mv2_dp_provenance=provenance,
        recovery=recovery,
        terminal_boundary=terminal,
        portfolio_admitted=portfolio_admitted,
        portfolio_active_sum=portfolio_active_sum,
    )

    return StagedProductiveN5RuntimeControlPlaneResultV1(
        terminal_boundary=terminal,
        cardinality=cardinality,
        aggregate=aggregate,
        recovery=recovery,
        audit=audit,
        orchestrator_result=orch,
        external_effect_authorized=False,
        post_allowed=False,
    )
