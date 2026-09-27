"""Governed F1/M9 productive runtime apply start (AUTHORIZED_PRODUCTIVE_APPLY; no activation)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.authorized_productive_parameter_seam_v1 import (
    AuthorizedProductiveParameterSeamBindRequestV1,
    STATUS_BOUND as SEAM_STATUS_BOUND,
    bind_authorized_productive_parameter_seam_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.f1_m9_bounded_threshold_enforcement_mv2_consumer_v1 import (
    threshold_enforcement_authorized_v1,
)
from src.governance.f1_m9_owner_apply_record_materialization_v1 import (
    STATUS_MATERIALIZED as OWNER_APPLY_RECORD_MATERIALIZED,
    materialize_owner_apply_record_when_canonical_candidate_resolved_v1,
)
from src.governance.f1_m9_owner_threshold_value_ratification_artifacts_v1 import (
    load_owner_threshold_record_artifact_v1,
)
from src.governance.f1_m9_owner_threshold_value_record_materialization_v1 import (
    STATUS_MATERIALIZED as THRESHOLD_RECORD_MATERIALIZED,
    materialize_owner_threshold_value_record_when_owner_ratification_authorized_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_post_real_campaign_optimization_governance_ingress_v1 import (
    build_f1_m9_post_real_campaign_optimization_governance_ingress_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_bounded_completion_v1 import (
    DEFAULT_RUNTIME_AUTHORIZATION_ID,
    DEFAULT_SELECTED_CANDIDATE_ID,
    DEFAULT_SELECTED_MAX_AGE_SECONDS,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    F1M9ProductiveApplyExecutionPhaseV1,
    F1M9ProductiveApplyExecutionRequestV1,
    STATUS_PRODUCTIVE_APPLY_COMPLETED,
    evaluate_f1_m9_productive_apply_execution_boundary_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
from src.governance.f1_m9_productive_runtime_apply_start_artifacts_v1 import (
    OWNER_RUNTIME_APPLY_START_WP_DECISION_CONFIG,
    RUNTIME_APPLY_START_CONTINUATION_DECISION_CONFIG,
    load_owner_runtime_apply_start_wp_decision_v1,
    persist_runtime_apply_start_evidence_artifact_v1,
)
from src.governance.f1_m9_prospective_real_campaign_durable_evidence_verification_v1 import (
    verify_f1_m9_prospective_real_campaign_durable_evidence_v1,
)
from src.governance.f1_m9_scoped_owner_threshold_value_authority_v1 import (
    F1M9ScopedOwnerThresholdValueAdjudicationRequestV1,
    evaluate_f1_m9_scoped_owner_threshold_value_authority_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
)
from src.governance.governed_f1_m9_scoped_owner_productive_runtime_apply_start_evidence_v1 import (
    F1M9RuntimeApplyStartPhaseStateV1,
    build_runtime_apply_start_state_evidence_v1,
)
from src.governance.governed_f1_m9_scoped_owner_threshold_value_ratification_closure_v1 import (
    prove_governed_f1_m9_scoped_owner_threshold_value_ratification_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    STATUS_TRANSPORT_READY,
    resolve_governed_runtime_seam_for_presence_gate_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    EXTERNAL_EFFECT,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.real_p4_to_f1_m9_apply_lineage_join_v1 import JOIN_STATUS_NOT_CANONICAL
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    parse_aware_utc_datetime_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_bounded_completion_v1 import (
    DECISION_CONFIG as HANDOFF_DECISION_CONFIG,
)
from src.governance.f1_m9_owner_threshold_value_ratification_artifacts_v1 import (
    OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = (
    "governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_F1_M9_SCOPED_OWNER_PRODUCTIVE_RUNTIME_APPLY_START_REAL_MECHANICAL_CONTINUATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_F1_M9_SCOPED_OWNER_PRODUCTIVE_RUNTIME_APPLY_START_REAL_MECHANICAL_CONTINUATION_V1.md"
)
DECISION_CONFIG: Final[str] = RUNTIME_APPLY_START_CONTINUATION_DECISION_CONFIG
OWNER_WP_DECISION_CONFIG: Final[str] = OWNER_RUNTIME_APPLY_START_WP_DECISION_CONFIG

RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS: Final[int] = 600
REAL_P4_TO_F1_M9_JOIN_STATUS: Final[str] = JOIN_STATUS_NOT_CANONICAL
PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class GovernedF1M9RuntimeApplyStartRequestV1:
    apply_ledger_paths: F1M9ProductiveApplyLedgerPathsV1
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1
    repo_root: Path | None = None
    persist_durable_evidence: bool = False
    evaluation_time_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class GovernedF1M9RuntimeApplyStartResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    productive_apply_occurred: bool
    runtime_apply_started: bool
    configuration_runtime_applied: bool
    ratified_value_lineage_valid: bool
    real_p4_to_f1_m9_join_status: str
    productive_activation_authorized: bool
    external_effect: bool
    owner_apply_record_digest: str | None
    owner_threshold_record_digest: str | None
    threshold_enforcement_mechanical_continuation: bool
    presence_gate_transport_ready: bool
    apply_start_evidence: Any
    bound_seam_record: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocking_reasons": list(self.blocking_reasons),
            "configuration_runtime_applied": self.configuration_runtime_applied,
            "decision_code": self.decision_code,
            "external_effect": self.external_effect,
            "owner_apply_record_digest": self.owner_apply_record_digest,
            "owner_threshold_record_digest": self.owner_threshold_record_digest,
            "presence_gate_transport_ready": self.presence_gate_transport_ready,
            "productive_activation_authorized": self.productive_activation_authorized,
            "productive_apply_occurred": self.productive_apply_occurred,
            "ratified_value_lineage_valid": self.ratified_value_lineage_valid,
            "real_p4_to_f1_m9_join_status": self.real_p4_to_f1_m9_join_status,
            "runtime_apply_started": self.runtime_apply_started,
            "status": self.status,
            "threshold_enforcement_mechanical_continuation": (
                self.threshold_enforcement_mechanical_continuation
            ),
            "bound_seam_record_digest": (
                str(self.bound_seam_record.get("seam_digest"))
                if isinstance(self.bound_seam_record, Mapping)
                and self.bound_seam_record.get("seam_digest")
                else None
            ),
        }


def _derive_runtime_apply_started_v1(
    *,
    productive_apply_occurred: bool,
    configuration_record: dict[str, Any] | None,
) -> bool:
    if not productive_apply_occurred or configuration_record is None:
        return False
    return configuration_record.get("runtime_applied") is True


def run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1(
    request: GovernedF1M9RuntimeApplyStartRequestV1,
) -> GovernedF1M9RuntimeApplyStartResultV1:
    root = request.repo_root or _REPO_ROOT
    now = request.evaluation_time_utc or datetime.now(timezone.utc)

    if not prove_governed_f1_m9_scoped_owner_threshold_value_ratification_v1(repo_root=root):
        return _reject(("POST_6887_THRESHOLD_RATIFICATION_NOT_PROVEN",))

    try:
        owner_wp = load_owner_runtime_apply_start_wp_decision_v1(repo_root=root)
    except (FileNotFoundError, ValueError) as exc:
        return _reject((str(exc),))

    if owner_wp.get("governed_productive_runtime_apply_start_authorized") is not True:
        return _reject(("RUNTIME_APPLY_START_NOT_OWNER_AUTHORIZED",))

    bound_threshold = str(owner_wp.get("ratified_threshold_record_digest_bound") or "")
    bound_apply = str(owner_wp.get("authorized_owner_apply_record_digest") or "")
    if not is_valid_sha256_hex(bound_threshold) or not is_valid_sha256_hex(bound_apply):
        return _reject(("OWNER_WP_DIGEST_BINDINGS_INVALID",))

    if int(owner_wp.get("threshold_numeric_max_age_seconds", -1)) != (
        RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS
    ):
        return _reject(("RATIFIED_THRESHOLD_VALUE_MISMATCH",))

    durable_threshold = load_owner_threshold_record_artifact_v1(repo_root=root)
    if durable_threshold is None:
        return _reject(("DURABLE_THRESHOLD_RECORD_MISSING",))
    if str(durable_threshold.get("threshold_value_authorization_record_digest") or "") != (
        bound_threshold
    ):
        return _reject(("DURABLE_THRESHOLD_DIGEST_MISMATCH",))

    threshold_wp = json.loads((root / OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG).read_text())
    authorizer = str(
        threshold_wp.get("authorizer_identity")
        or "OWNER_GO_F1_M9_THRESHOLD_VALUE_RATIFICATION_600_SECONDS"
    )

    verification = verify_f1_m9_prospective_real_campaign_durable_evidence_v1(
        repo_root=root,
        expected_runtime_authorization_id=DEFAULT_RUNTIME_AUTHORIZATION_ID,
        expected_selected_candidate_id=DEFAULT_SELECTED_CANDIDATE_ID,
        expected_selected_max_age_seconds=DEFAULT_SELECTED_MAX_AGE_SECONDS,
    )
    if not verification.verified:
        return _reject(tuple(verification.reason_codes))

    ingress = build_f1_m9_post_real_campaign_optimization_governance_ingress_v1(
        verification=verification,
        repo_root=root,
    )
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
        authorizer_identity=authorizer,
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
    registry = load_scoped_join_registry_v1(repo_root=root)
    binding = evaluate_f1_m9_per_ingress_authorization_binding_v1(
        ingress=ingress,
        owner_input=owner_input,
        registry_digest=str(registry["registry_digest"]),
    )

    handoff_decision = json.loads((root / HANDOFF_DECISION_CONFIG).read_text(encoding="utf-8"))
    not_before = parse_aware_utc_datetime_v1(
        handoff_decision["owner_apply_not_before_utc"],
        field_name="owner_apply_not_before_utc",
    )
    expires_at = parse_aware_utc_datetime_v1(
        handoff_decision["owner_apply_expires_at_utc"],
        field_name="owner_apply_expires_at_utc",
    )

    mat_apply = materialize_owner_apply_record_when_canonical_candidate_resolved_v1(
        registry_digest=str(registry["registry_digest"]),
        ingress_digest=str(ingress["ingress_digest"]),
        binding=binding,
        authorization=authorization,
        configuration=configuration,
        not_before=not_before,
        expires_at=expires_at,
        repo_root=root,
    )
    if (
        mat_apply.materialization_status != OWNER_APPLY_RECORD_MATERIALIZED
        or mat_apply.owner_apply_input is None
    ):
        return _reject(tuple(mat_apply.reason_codes))

    apply_input = mat_apply.owner_apply_input
    apply_digest = apply_input.owner_apply_authorization_record_digest
    if apply_digest != bound_apply:
        return _reject(("CANONICAL_APPLY_DIGEST_MISMATCH_POST_6887_LINEAGE",))

    execution = evaluate_f1_m9_productive_apply_execution_boundary_v1(
        F1M9ProductiveApplyExecutionRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=configuration,
            registry_digest=str(registry["registry_digest"]),
            ledger_paths=request.apply_ledger_paths,
            execution_phase=F1M9ProductiveApplyExecutionPhaseV1.AUTHORIZED_PRODUCTIVE_APPLY,
            evaluation_time_utc=now,
        ),
        repo_root=root,
    )
    if execution.execution_status != STATUS_PRODUCTIVE_APPLY_COMPLETED:
        return _reject(tuple(execution.reason_codes))

    config_after_apply = execution.configuration_after_execution
    if config_after_apply is None or config_after_apply.configuration_record is None:
        return _reject(("CONFIGURATION_AFTER_APPLY_MISSING",))

    cfg_record = dict(config_after_apply.configuration_record)
    runtime_apply_started = _derive_runtime_apply_started_v1(
        productive_apply_occurred=execution.productive_apply_occurred,
        configuration_record=cfg_record,
    )
    if not runtime_apply_started:
        return _reject(("RUNTIME_APPLY_STARTED_NOT_DERIVED",))

    mat_threshold = materialize_owner_threshold_value_record_when_owner_ratification_authorized_v1(
        registry_digest=str(registry["registry_digest"]),
        binding_digest=binding.binding_digest,
        applied_configuration=config_after_apply,
        apply_input=apply_input,
        repo_root=root,
    )
    if (
        mat_threshold.materialization_status != THRESHOLD_RECORD_MATERIALIZED
        or mat_threshold.owner_threshold_input is None
    ):
        return _reject(tuple(mat_threshold.reason_codes))

    threshold_input = mat_threshold.owner_threshold_input
    threshold_record_digest = threshold_input.owner_threshold_authorization_record_digest
    if threshold_record_digest != bound_threshold:
        return _reject(("THRESHOLD_RECORD_LINEAGE_MISMATCH",))

    threshold_result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
        F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
            owner_threshold_input=threshold_input,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=config_after_apply,
            registry_digest=str(registry["registry_digest"]),
            apply_ledger_paths=request.apply_ledger_paths,
            threshold_ledger_paths=request.threshold_ledger_paths,
            evaluation_time_utc=now,
        )
    )
    if not threshold_result.threshold_value_authorized:
        return _reject(tuple(threshold_result.reason_codes))

    config_after_threshold = threshold_result.configuration_after_threshold
    if config_after_threshold is None or config_after_threshold.configuration_record is None:
        return _reject(("THRESHOLD_CONFIGURATION_AFTER_MISSING",))

    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=config_after_threshold)
    )
    if seam.seam_status != SEAM_STATUS_BOUND or seam.seam_record is None:
        return _reject(tuple(seam.reason_codes))

    transport = resolve_governed_runtime_seam_for_presence_gate_v1(dict(seam.seam_record))
    presence_ready = transport.transport_status == STATUS_TRANSPORT_READY

    enforcement_ready = threshold_enforcement_authorized_v1(repo_root=root) and presence_ready
    enforcement_ok = enforcement_ready

    evidence = build_runtime_apply_start_state_evidence_v1(
        phase_state=F1M9RuntimeApplyStartPhaseStateV1.COMPLETED,
        reason_codes=("F1_M9_RUNTIME_APPLY_START_CONTINUATION_COMPLETE",),
        productive_apply_occurred=execution.productive_apply_occurred,
        runtime_apply_started=runtime_apply_started,
        configuration_runtime_applied=cfg_record.get("runtime_applied") is True,
        owner_apply_record_digest=apply_digest,
        owner_threshold_record_digest=bound_threshold,
        threshold_value_authorized=True,
        threshold_numeric_max_age_seconds=float(RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS),
        threshold_enforcement_mechanical_continuation=enforcement_ok,
        presence_gate_transport_ready=presence_ready,
        productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
    )

    if request.persist_durable_evidence:
        persist_runtime_apply_start_evidence_artifact_v1(evidence.to_dict(), repo_root=root)

    return GovernedF1M9RuntimeApplyStartResultV1(
        status="CONTINUATION_COMPLETE",
        decision_code="F1_M9_RUNTIME_APPLY_START_CONTINUATION_COMPLETE",
        blocking_reasons=(),
        productive_apply_occurred=execution.productive_apply_occurred,
        runtime_apply_started=runtime_apply_started,
        configuration_runtime_applied=cfg_record.get("runtime_applied") is True,
        ratified_value_lineage_valid=True,
        real_p4_to_f1_m9_join_status=REAL_P4_TO_F1_M9_JOIN_STATUS,
        productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
        external_effect=EXTERNAL_EFFECT is True,
        owner_apply_record_digest=apply_digest,
        owner_threshold_record_digest=bound_threshold,
        threshold_enforcement_mechanical_continuation=enforcement_ok,
        presence_gate_transport_ready=presence_ready,
        apply_start_evidence=evidence,
        bound_seam_record=dict(seam.seam_record),
    )


def _reject(reasons: tuple[str, ...]) -> GovernedF1M9RuntimeApplyStartResultV1:
    evidence = build_runtime_apply_start_state_evidence_v1(
        phase_state=F1M9RuntimeApplyStartPhaseStateV1.DENIED,
        reason_codes=reasons,
        productive_apply_occurred=False,
        runtime_apply_started=False,
        configuration_runtime_applied=False,
        owner_apply_record_digest=None,
        owner_threshold_record_digest=None,
        threshold_value_authorized=False,
        threshold_numeric_max_age_seconds=None,
        threshold_enforcement_mechanical_continuation=False,
        presence_gate_transport_ready=False,
        productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
    )
    return GovernedF1M9RuntimeApplyStartResultV1(
        status="REJECTED",
        decision_code="F1_M9_RUNTIME_APPLY_START_DENIED",
        blocking_reasons=reasons,
        productive_apply_occurred=False,
        runtime_apply_started=False,
        configuration_runtime_applied=False,
        ratified_value_lineage_valid=False,
        real_p4_to_f1_m9_join_status=REAL_P4_TO_F1_M9_JOIN_STATUS,
        productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
        external_effect=EXTERNAL_EFFECT is True,
        owner_apply_record_digest=None,
        owner_threshold_record_digest=None,
        threshold_enforcement_mechanical_continuation=False,
        presence_gate_transport_ready=False,
        apply_start_evidence=evidence,
        bound_seam_record=None,
    )


def prove_continuation_authority_invariants_v1() -> bool:
    return (
        PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and EXTERNAL_EFFECT is False
        and REAL_P4_TO_F1_M9_JOIN_STATUS == JOIN_STATUS_NOT_CANONICAL
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        NORMATIVE_SPEC,
        "src/governance/governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1.py",
        "tests/governance/test_governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    return (
        decision.get("workpackage_id") == WORKPACKAGE_ID
        and owner.get("governed_productive_runtime_apply_start_authorized") is True
        and decision.get("productive_activation_authorized") is False
        and int(decision.get("ratified_threshold_numeric_max_age_seconds", -1))
        == RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS
    )


__all__ = [
    "DECISION_CONFIG",
    "GovernedF1M9RuntimeApplyStartRequestV1",
    "GovernedF1M9RuntimeApplyStartResultV1",
    "NORMATIVE_SPEC",
    "OWNER_WP_DECISION_CONFIG",
    "PRODUCTIVE_ACTIVATION_AUTHORIZED",
    "RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS",
    "REAL_P4_TO_F1_M9_JOIN_STATUS",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "prove_continuation_authority_invariants_v1",
    "prove_continuation_decision_files_v1",
    "run_governed_f1_m9_scoped_owner_productive_runtime_apply_start_continuation_v1",
]
