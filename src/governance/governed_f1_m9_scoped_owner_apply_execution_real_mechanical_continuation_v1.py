"""Real P4 materialization boundary + canonical F1/M9 scoped Owner Apply execution proof.

Real runtime proves the #6885 seam-scoped materialization record. F1/M9 Owner Apply
execution uses the canonical per-ingress M10 chain (separate plane). Cross-plane join is
fail-closed (not canonically established).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    ExplicitProductiveAuthorizationResultV1,
    OwnerExplicitProductiveAuthorizationInputV1,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
    build_owner_apply_authorization_input_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressAuthorizationBindingV1,
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    F1M9ProductiveApplyExecutionPhaseV1,
    F1M9ProductiveApplyExecutionRequestV1,
    STATUS_EXECUTION_READY,
    evaluate_f1_m9_productive_apply_execution_boundary_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
    RUNTIME_APPLY_AUTHORITY_VALUE,
)
from src.governance.governed_f1_m9_scoped_owner_apply_execution_evidence_v1 import (
    F1M9ApplyExecutionPhaseStateV1,
    F1M9ApplyExecutionStateEvidenceV1,
    build_apply_execution_state_evidence_v1,
)
from src.governance.governed_p4_l6_seam_to_runtime_apply_materialization_real_mechanical_continuation_v1 import (
    RealP4RuntimeApplyMaterializationContinuationRequestV1,
    run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    GovernedProductiveConfigurationResultV1,
    STATUS_MATERIALIZED,
    materialize_governed_productive_configuration_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionRequestV1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    OptimizationProposalGovernanceAdmissionResultV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.real_p4_to_f1_m9_apply_lineage_join_v1 import (
    JOIN_STATUS_NOT_CANONICAL,
    evaluate_real_p4_to_f1_m9_apply_join_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    A_RUNTIME_IMPLEMENTATION_AUTHORIZED as P2_A_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)
from src.governance.master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.constants_v1 import (
    B_RUNTIME_IMPLEMENTATION_AUTHORIZED as P3_B_RUNTIME_IMPLEMENTATION_AUTHORIZED,
)

SCHEMA_VERSION: Final[str] = (
    "governed_f1_m9_scoped_owner_apply_execution_real_mechanical_continuation_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_F1_M9_SCOPED_OWNER_APPLY_EXECUTION_REAL_MECHANICAL_CONTINUATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/GOVERNED_F1_M9_SCOPED_OWNER_APPLY_EXECUTION_REAL_MECHANICAL_CONTINUATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_f1_m9_scoped_owner_apply_execution_real_mechanical_continuation_v1_decision_v1.json"
)
OWNER_WP_DECISION_CONFIG: Final[str] = (
    "config/governance/governed_f1_m9_scoped_owner_apply_execution_wp_v1_owner_decision_v1.json"
)

F1_M9_APPLY_PATH_STATUS: Final[str] = "PROVEN_CANONICAL_PER_INGRESS_EXECUTION_PROOF"
REAL_P4_TO_F1_M9_JOIN_STATUS: Final[str] = JOIN_STATUS_NOT_CANONICAL
VALUE_RATIFICATION_REQUIRED_FOR_THRESHOLD_HOT_PATH: Final[bool] = True

RUNTIME_APPLY_STARTED: Final[bool] = False
RUNTIME_APPLY_COMPLETED: Final[bool] = False
PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False
EXTERNAL_EFFECT: Final[bool] = False
COMPONENT_B_ACTIVATED: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class F1M9PerIngressExecutionContextV1:
    ingress: Mapping[str, Any]
    admission: OptimizationProposalGovernanceAdmissionResultV1
    owner_input: OwnerExplicitProductiveAuthorizationInputV1
    binding: PerIngressAuthorizationBindingV1
    authorization: ExplicitProductiveAuthorizationResultV1
    configuration: GovernedProductiveConfigurationResultV1
    registry_digest: str
    ledger_paths: F1M9ProductiveApplyLedgerPathsV1
    offline_plane_workspace: Path
    real_upstream_source_used: bool = False
    ddo_fixture_state_used: bool = False


@dataclass(frozen=True)
class GovernedF1M9ApplyExecutionContinuationRequestV1:
    projection_request: GovernedRuntimePrimaryProjectionRequestV1
    f1_m9_context: F1M9PerIngressExecutionContextV1
    replay_seed: int | None = None
    ddo_fixture_learning_state: dict[str, Any] | None = None
    repo_root: Path | None = None


@dataclass(frozen=True)
class GovernedF1M9ApplyExecutionContinuationResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    real_p4_materialization_status: str | None
    f1_m9_apply_path_status: str | None
    real_p4_to_f1_m9_join_status: str | None
    target_id: str | None
    candidate_domain: str | None
    exact_applied_value_representation: str | None
    value_ratification_status: str | None
    apply_execution_evidence: F1M9ApplyExecutionStateEvidenceV1 | None
    execution_boundary_status: str | None
    lineage_chain: tuple[str, ...] = field(default_factory=tuple)
    real_upstream_source_used: bool = False
    p4_l6_real_seam_used: bool = False
    runtime_materialization_record_used: bool = False
    f1_m9_canonical_apply_owner_used: bool = False
    f1_m9_value_authority_valid: bool = False
    apply_authorization_valid: bool = False
    apply_started: bool = False
    configuration_runtime_applied: bool = False
    apply_completed: bool = False
    configuration_materialized: bool = False
    configuration_applied: bool = False
    lineage_join_valid: bool = False
    ddo_fixture_state_used_on_real_path: bool = False
    f1_m9_per_ingress_real_upstream_source_used: bool = False


def build_owner_apply_input_from_configuration_v1(
    *,
    configuration: GovernedProductiveConfigurationResultV1,
    binding: PerIngressAuthorizationBindingV1,
    registry_digest: str,
) -> OwnerApplyAuthorizationInputV1:
    config = configuration.configuration_record
    if config is None:
        raise ValueError("CONFIGURATION_RECORD_MISSING")
    contract = build_productive_target_contract_v1()
    now = datetime.now(timezone.utc)
    return build_owner_apply_authorization_input_v1(
        registry_digest=registry_digest,
        ingress_digest=str(config["ingress_digest"]),
        binding_digest=binding.binding_digest,
        owner_authorization_record_digest=str(config["owner_authorization_record_digest"]),
        authorization_id=str(config["authorization_id"]),
        authorization_digest=str(config["authorization_digest"]),
        configuration_id=str(config["configuration_id"]),
        configuration_digest=str(config["configuration_digest"]),
        candidate_parameter_value_digest=str(config["candidate_parameter_value_digest"]),
        productive_target_id=str(config["productive_target_id"]),
        productive_target_version=str(config["productive_target_version"]),
        productive_target_contract_digest=str(contract["contract_digest"]),
        not_before=(now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        expires_at=(now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def execute_f1_m9_scoped_owner_apply_execution_proof_v1(
    *,
    context: F1M9PerIngressExecutionContextV1,
    repo_root: Path | None = None,
) -> tuple[F1M9ApplyExecutionStateEvidenceV1, str, GovernedProductiveConfigurationResultV1]:
    """Canonical F1/M9 per-ingress EXECUTION_PROOF (runtime_applied; no productive activation)."""
    if context.configuration.configuration_status != STATUS_MATERIALIZED:
        evidence = build_apply_execution_state_evidence_v1(
            phase_state=F1M9ApplyExecutionPhaseStateV1.APPLY_DENIED,
            reason_codes=("CONFIGURATION_NOT_MATERIALIZED",),
            configuration_materialized=False,
            apply_authorized=False,
            apply_started=False,
            configuration_runtime_applied=False,
            apply_completed=False,
            threshold_value_ratified=False,
            candidate_value_applied=False,
            owner_apply_record_digest=None,
            configuration_digest=None,
        )
        return evidence, "DENIED_FAIL_CLOSED", context.configuration

    apply_input = build_owner_apply_input_from_configuration_v1(
        configuration=context.configuration,
        binding=context.binding,
        registry_digest=context.registry_digest,
    )
    execution = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=context.binding,
            authorization=context.authorization,
            configuration=context.configuration,
            registry_digest=context.registry_digest,
            ledger_paths=context.ledger_paths,
            execution_phase=F1M9ProductiveApplyExecutionPhaseV1.EXECUTION_PROOF,
        ),
        repo_root=repo_root,
    )
    config_after = execution.configuration_after_execution or context.configuration
    record = config_after.configuration_record
    runtime_applied = bool(record.get("runtime_applied")) if record else False
    threshold_ratified = bool(record.get("threshold_value_ratified")) if record else False
    candidate_applied = bool(record.get("candidate_value_applied")) if record else False

    ok = (
        execution.execution_status == STATUS_EXECUTION_READY
        and execution.productive_apply_authorized
        and runtime_applied
        and execution.productive_apply_occurred is False
    )
    if not ok:
        evidence = build_apply_execution_state_evidence_v1(
            phase_state=F1M9ApplyExecutionPhaseStateV1.APPLY_DENIED,
            reason_codes=tuple(execution.reason_codes) or ("F1_M9_APPLY_EXECUTION_DENIED",),
            configuration_materialized=True,
            apply_authorized=execution.productive_apply_authorized,
            apply_started=False,
            configuration_runtime_applied=runtime_applied,
            apply_completed=False,
            threshold_value_ratified=threshold_ratified,
            candidate_value_applied=candidate_applied,
            owner_apply_record_digest=execution.owner_apply_authorization_record_digest,
            configuration_digest=str(config_after.configuration_digest or ""),
        )
        return evidence, execution.execution_status, config_after

    evidence = build_apply_execution_state_evidence_v1(
        phase_state=F1M9ApplyExecutionPhaseStateV1.APPLY_COMPLETED,
        reason_codes=("F1_M9_SCOPED_OWNER_APPLY_EXECUTION_PROOF_COMPLETE",),
        configuration_materialized=True,
        apply_authorized=True,
        apply_started=True,
        configuration_runtime_applied=True,
        apply_completed=True,
        threshold_value_ratified=threshold_ratified,
        candidate_value_applied=candidate_applied,
        owner_apply_record_digest=execution.owner_apply_authorization_record_digest,
        configuration_digest=str(config_after.configuration_digest or ""),
    )
    return evidence, execution.execution_status, config_after


def run_governed_f1_m9_scoped_owner_apply_execution_continuation_v1(
    request: GovernedF1M9ApplyExecutionContinuationRequestV1,
) -> GovernedF1M9ApplyExecutionContinuationResultV1:
    root = request.repo_root or _REPO_ROOT
    p4 = run_real_runtime_p4_l6_to_runtime_apply_materialization_continuation_v1(
        RealP4RuntimeApplyMaterializationContinuationRequestV1(
            projection_request=request.projection_request,
            replay_seed=request.replay_seed,
            ddo_fixture_learning_state=request.ddo_fixture_learning_state,
            repo_root=root,
        )
    )
    lineage = p4.lineage_chain
    if p4.status != "CONTINUATION_COMPLETE":
        return GovernedF1M9ApplyExecutionContinuationResultV1(
            status="REJECTED",
            decision_code=p4.decision_code,
            blocking_reasons=p4.blocking_reasons,
            real_p4_materialization_status="REJECTED",
            f1_m9_apply_path_status=None,
            real_p4_to_f1_m9_join_status=None,
            target_id=None,
            candidate_domain=None,
            exact_applied_value_representation=None,
            value_ratification_status=None,
            apply_execution_evidence=None,
            execution_boundary_status=None,
            lineage_chain=lineage,
            real_upstream_source_used=p4.real_upstream_source_used,
            p4_l6_real_seam_used=p4.p4_l6_real_seam_used,
            ddo_fixture_state_used_on_real_path=p4.ddo_fixture_state_used,
        )

    ctx = request.f1_m9_context
    join = evaluate_real_p4_to_f1_m9_apply_join_v1(
        materialization_record=p4.materialization_record,
        configuration=ctx.configuration,
    )
    if join.join_permitted:
        return GovernedF1M9ApplyExecutionContinuationResultV1(
            status="REJECTED",
            decision_code="REAL_P4_F1_M9_JOIN_UNEXPECTEDLY_PERMITTED",
            blocking_reasons=join.reason_codes,
            real_p4_materialization_status="PROVEN_REAL_MECHANICAL_PATH",
            f1_m9_apply_path_status=None,
            real_p4_to_f1_m9_join_status=join.join_status,
            target_id=PRODUCTIVE_TARGET_ID,
            candidate_domain=None,
            exact_applied_value_representation=None,
            value_ratification_status=None,
            apply_execution_evidence=None,
            execution_boundary_status=None,
            lineage_chain=lineage,
            real_upstream_source_used=True,
            p4_l6_real_seam_used=True,
            runtime_materialization_record_used=p4.materialization_record is not None,
            ddo_fixture_state_used_on_real_path=False,
        )

    evidence, boundary_status, config_after = execute_f1_m9_scoped_owner_apply_execution_proof_v1(
        context=ctx,
        repo_root=root,
    )
    config_record = config_after.configuration_record
    candidate_digest = (
        str(config_record.get("candidate_parameter_value_digest") or "") if config_record else ""
    )
    value_status = (
        "THRESHOLD_HOT_PATH_NOT_RATIFIED"
        if VALUE_RATIFICATION_REQUIRED_FOR_THRESHOLD_HOT_PATH
        else "UNKNOWN"
    )
    extended = (
        *lineage,
        f"f1_m9_apply_execution://{evidence.execution_evidence_digest}",
        f"real_p4_f1_m9_join://{join.join_status}",
    )
    apply_ok = evidence.phase_state == F1M9ApplyExecutionPhaseStateV1.APPLY_COMPLETED
    return GovernedF1M9ApplyExecutionContinuationResultV1(
        status="CONTINUATION_COMPLETE" if apply_ok else "REJECTED",
        decision_code=(
            "F1_M9_SCOPED_OWNER_APPLY_EXECUTION_CONTINUATION_COMPLETE"
            if apply_ok
            else evidence.phase_state.value
        ),
        blocking_reasons=() if apply_ok else evidence.reason_codes,
        real_p4_materialization_status="PROVEN_REAL_MECHANICAL_PATH",
        f1_m9_apply_path_status=F1_M9_APPLY_PATH_STATUS,
        real_p4_to_f1_m9_join_status=join.join_status,
        target_id=PRODUCTIVE_TARGET_ID,
        candidate_domain="F1_M9_VOLATILITY_NUMERIC_MAX_AGE_OWNER_EXPLICIT_INGRESS",
        exact_applied_value_representation=(
            f"candidate_parameter_value_digest:{candidate_digest}" if candidate_digest else None
        ),
        value_ratification_status=value_status,
        apply_execution_evidence=evidence,
        execution_boundary_status=boundary_status,
        lineage_chain=extended,
        real_upstream_source_used=True,
        p4_l6_real_seam_used=True,
        runtime_materialization_record_used=p4.materialization_record is not None,
        f1_m9_canonical_apply_owner_used=True,
        f1_m9_value_authority_valid=not candidate_digest == "",
        apply_authorization_valid=evidence.apply_authorized,
        apply_started=evidence.apply_started,
        configuration_runtime_applied=evidence.configuration_runtime_applied,
        apply_completed=evidence.apply_completed,
        configuration_materialized=evidence.configuration_materialized,
        configuration_applied=evidence.configuration_runtime_applied,
        lineage_join_valid=p4.lineage_join_valid and apply_ok,
        ddo_fixture_state_used_on_real_path=False,
        f1_m9_per_ingress_real_upstream_source_used=ctx.real_upstream_source_used,
    )


def build_f1_m9_per_ingress_context_from_admitted_ingress_v1(
    *,
    ingress: Mapping[str, Any],
    workspace: Path,
    repo_root: Path | None = None,
    real_upstream_source_used: bool = False,
    ddo_fixture_state_used: bool = False,
) -> F1M9PerIngressExecutionContextV1:
    """Build canonical F1/M9 per-ingress chain artifacts (offline plane workspace)."""
    root = repo_root or _REPO_ROOT
    registry = load_scoped_join_registry_v1(repo_root=root)
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    binding = evaluate_f1_m9_per_ingress_authorization_binding_v1(
        ingress=ingress,
        owner_input=owner_input,
        registry_digest=str(registry["registry_digest"]),
    )
    authorization = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    configuration = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    rev = workspace / "revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    ledger_paths = F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=workspace / "apply.jsonl",
        revocation_ledger_path=rev,
    )
    return F1M9PerIngressExecutionContextV1(
        ingress=ingress,
        admission=admission,
        owner_input=owner_input,
        binding=binding,
        authorization=authorization,
        configuration=configuration,
        registry_digest=str(registry["registry_digest"]),
        ledger_paths=ledger_paths,
        offline_plane_workspace=workspace,
        real_upstream_source_used=real_upstream_source_used,
        ddo_fixture_state_used=ddo_fixture_state_used,
    )


def prove_continuation_authority_invariants_v1() -> bool:
    return (
        RUNTIME_APPLY_STARTED is False
        and RUNTIME_APPLY_COMPLETED is False
        and PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and EXTERNAL_EFFECT is False
        and COMPONENT_B_ACTIVATED is False
        and P2_A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
        and P3_B_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
        and REAL_P4_TO_F1_M9_JOIN_STATUS == JOIN_STATUS_NOT_CANONICAL
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        NORMATIVE_SPEC,
        "src/governance/governed_f1_m9_scoped_owner_apply_execution_real_mechanical_continuation_v1.py",
        "src/governance/real_p4_to_f1_m9_apply_lineage_join_v1.py",
        "tests/governance/test_governed_f1_m9_scoped_owner_apply_execution_real_mechanical_continuation_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    return (
        decision.get("workpackage_id") == WORKPACKAGE_ID
        and owner.get("f1_m9_scoped_owner_apply_execution_authorized") is True
        and decision.get("productive_activation_authorized") is False
    )


__all__ = [
    "DECISION_CONFIG",
    "F1M9PerIngressExecutionContextV1",
    "F1_M9_APPLY_PATH_STATUS",
    "GovernedF1M9ApplyExecutionContinuationRequestV1",
    "GovernedF1M9ApplyExecutionContinuationResultV1",
    "NORMATIVE_SPEC",
    "OWNER_WP_DECISION_CONFIG",
    "REAL_P4_TO_F1_M9_JOIN_STATUS",
    "RUNTIME_APPLY_COMPLETED",
    "RUNTIME_APPLY_STARTED",
    "SCHEMA_VERSION",
    "VALUE_RATIFICATION_REQUIRED_FOR_THRESHOLD_HOT_PATH",
    "WORKPACKAGE_ID",
    "build_f1_m9_per_ingress_context_from_admitted_ingress_v1",
    "build_owner_apply_input_from_configuration_v1",
    "execute_f1_m9_scoped_owner_apply_execution_proof_v1",
    "prove_continuation_authority_invariants_v1",
    "prove_continuation_decision_files_v1",
    "run_governed_f1_m9_scoped_owner_apply_execution_continuation_v1",
]
