"""Canonical F1/M9 Owner threshold value ratification (600s Owner GO; no activation)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

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
from src.governance.f1_m9_owner_apply_record_materialization_v1 import (
    STATUS_MATERIALIZED as OWNER_APPLY_RECORD_MATERIALIZED,
    materialize_owner_apply_record_when_canonical_candidate_resolved_v1,
)
from src.governance.f1_m9_owner_threshold_value_ratification_artifacts_v1 import (
    OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG,
    THRESHOLD_RATIFICATION_CONTINUATION_DECISION_CONFIG,
    persist_owner_threshold_record_artifact_v1,
)
from src.governance.f1_m9_owner_threshold_value_record_materialization_v1 import (
    STATUS_MATERIALIZED as THRESHOLD_RECORD_MATERIALIZED,
    load_owner_threshold_ratification_wp_decision_v1,
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
from src.governance.f1_m9_prospective_real_campaign_durable_evidence_verification_v1 import (
    verify_f1_m9_prospective_real_campaign_durable_evidence_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
    F1M9ScopedOwnerApplyAdjudicationRequestV1,
    evaluate_f1_m9_scoped_owner_productive_apply_v1,
)
from src.governance.f1_m9_scoped_owner_threshold_value_authority_v1 import (
    F1M9ScopedOwnerThresholdValueAdjudicationRequestV1,
    evaluate_f1_m9_scoped_owner_threshold_value_authority_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
)
from src.governance.governed_f1_m9_scoped_owner_threshold_value_ratification_evidence_v1 import (
    F1M9ThresholdRatificationPhaseStateV1,
    F1M9ThresholdValueRatificationStateEvidenceV1,
    build_threshold_ratification_state_evidence_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
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
from src.governance.authorized_productive_parameter_seam_v1 import (
    resolve_age_policy_from_authorized_seam_record_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    THRESHOLD_STATUS_RATIFIED_NUMERIC,
)

SCHEMA_VERSION: Final[str] = (
    "governed_f1_m9_scoped_owner_threshold_value_ratification_real_mechanical_continuation_v1"
)
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_RATIFICATION_REAL_MECHANICAL_CONTINUATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_RATIFICATION_REAL_MECHANICAL_CONTINUATION_V1.md"
)
DECISION_CONFIG: Final[str] = THRESHOLD_RATIFICATION_CONTINUATION_DECISION_CONFIG
OWNER_WP_DECISION_CONFIG: Final[str] = OWNER_THRESHOLD_RATIFICATION_WP_DECISION_CONFIG

PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False
REAL_P4_TO_F1_M9_JOIN_STATUS: Final[str] = JOIN_STATUS_NOT_CANONICAL
THRESHOLD_HOT_PATH_RATIFIED: Final[bool] = True
RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS: Final[int] = 600

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class GovernedF1M9ThresholdValueRatificationRequestV1:
    apply_ledger_paths: F1M9ProductiveApplyLedgerPathsV1
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1
    repo_root: Path | None = None
    persist_durable_threshold_record: bool = False
    evaluation_time_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class GovernedF1M9ThresholdValueRatificationResultV1:
    status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    threshold_hot_path_ratified: bool
    exact_value_authority_valid: bool
    f1_m9_value_binding_valid: bool
    real_p4_to_f1_m9_join_status: str
    productive_activation_authorized: bool
    external_effect: bool
    ratification_evidence: F1M9ThresholdValueRatificationStateEvidenceV1 | None
    configuration_digest_after_threshold: str | None
    owner_threshold_record_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocking_reasons": list(self.blocking_reasons),
            "configuration_digest_after_threshold": self.configuration_digest_after_threshold,
            "decision_code": self.decision_code,
            "exact_value_authority_valid": self.exact_value_authority_valid,
            "external_effect": self.external_effect,
            "f1_m9_value_binding_valid": self.f1_m9_value_binding_valid,
            "owner_threshold_record_digest": self.owner_threshold_record_digest,
            "productive_activation_authorized": self.productive_activation_authorized,
            "ratification_evidence": (
                None if self.ratification_evidence is None else self.ratification_evidence.to_dict()
            ),
            "real_p4_to_f1_m9_join_status": self.real_p4_to_f1_m9_join_status,
            "status": self.status,
            "threshold_hot_path_ratified": self.threshold_hot_path_ratified,
        }


def run_governed_f1_m9_scoped_owner_threshold_value_ratification_continuation_v1(
    request: GovernedF1M9ThresholdValueRatificationRequestV1,
) -> GovernedF1M9ThresholdValueRatificationResultV1:
    root = request.repo_root or _REPO_ROOT
    now = request.evaluation_time_utc or datetime.now(timezone.utc)

    try:
        owner_wp = load_owner_threshold_ratification_wp_decision_v1(repo_root=root)
    except (FileNotFoundError, ValueError) as exc:
        evidence = build_threshold_ratification_state_evidence_v1(
            phase_state=F1M9ThresholdRatificationPhaseStateV1.RATIFICATION_DENIED,
            reason_codes=(str(exc),),
            threshold_value_authorized=False,
            threshold_numeric_max_age_seconds=None,
            owner_threshold_record_digest=None,
            threshold_ledger_entry_digest=None,
            configuration_digest_after_threshold=None,
            scoped_owner_threshold_value_authorized=False,
            threshold_value_ratified=False,
            productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
        )
        return GovernedF1M9ThresholdValueRatificationResultV1(
            status="REJECTED",
            decision_code="OWNER_WP_DECISION_MISSING",
            blocking_reasons=(str(exc),),
            threshold_hot_path_ratified=False,
            exact_value_authority_valid=False,
            f1_m9_value_binding_valid=False,
            real_p4_to_f1_m9_join_status=REAL_P4_TO_F1_M9_JOIN_STATUS,
            productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
            external_effect=EXTERNAL_EFFECT is True,
            ratification_evidence=evidence,
            configuration_digest_after_threshold=None,
            owner_threshold_record_digest=None,
        )

    if owner_wp.get("owner_threshold_value_ratification_authorized") is not True:
        return _reject(("OWNER_THRESHOLD_VALUE_RATIFICATION_NOT_AUTHORIZED",))

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
        authorizer_identity=str(
            owner_wp.get("authorizer_identity") or "OWNER_GO_F1_M9_THRESHOLD_VALUE_RATIFICATION"
        ),
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
    from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
        parse_aware_utc_datetime_v1,
    )
    from src.governance.f1_m9_post_real_campaign_productive_handoff_bounded_completion_v1 import (
        DECISION_CONFIG as HANDOFF_DECISION_CONFIG,
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
    apply_result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=configuration,
            registry_digest=str(registry["registry_digest"]),
            ledger_paths=request.apply_ledger_paths,
        )
    )
    if (
        not apply_result.productive_apply_authorized
        or apply_result.configuration_after_apply is None
    ):
        return _reject(tuple(apply_result.reason_codes))
    applied_config = apply_result.configuration_after_apply

    mat_threshold = materialize_owner_threshold_value_record_when_owner_ratification_authorized_v1(
        registry_digest=str(registry["registry_digest"]),
        binding_digest=binding.binding_digest,
        applied_configuration=applied_config,
        apply_input=apply_input,
        repo_root=root,
    )
    if (
        mat_threshold.materialization_status != THRESHOLD_RECORD_MATERIALIZED
        or mat_threshold.owner_threshold_input is None
    ):
        return _reject(tuple(mat_threshold.reason_codes))

    threshold_input = mat_threshold.owner_threshold_input
    if request.persist_durable_threshold_record:
        artifact = dict(threshold_input.owner_threshold_authorization_record)
        artifact["owner_wp_decision_digest"] = mat_threshold.owner_wp_decision_digest
        persist_owner_threshold_record_artifact_v1(artifact, repo_root=root)

    threshold_result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
        F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
            owner_threshold_input=threshold_input,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=applied_config,
            registry_digest=str(registry["registry_digest"]),
            apply_ledger_paths=request.apply_ledger_paths,
            threshold_ledger_paths=request.threshold_ledger_paths,
            evaluation_time_utc=now,
        )
    )
    if not threshold_result.threshold_value_authorized:
        return _reject(tuple(threshold_result.reason_codes))

    config_after = threshold_result.configuration_after_threshold
    if config_after is None or config_after.configuration_record is None:
        return _reject(("THRESHOLD_CONFIGURATION_AFTER_MISSING",))

    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=config_after)
    )
    if seam.seam_status != SEAM_STATUS_BOUND or seam.seam_record is None:
        return _reject(tuple(seam.reason_codes))

    policy = resolve_age_policy_from_authorized_seam_record_v1(seam.seam_record)
    if policy.threshold_status != THRESHOLD_STATUS_RATIFIED_NUMERIC:
        return _reject(("SEAM_POLICY_NOT_RATIFIED_NUMERIC",))

    cfg_record = config_after.configuration_record
    evidence = build_threshold_ratification_state_evidence_v1(
        phase_state=F1M9ThresholdRatificationPhaseStateV1.RATIFICATION_COMPLETED,
        reason_codes=("F1_M9_THRESHOLD_VALUE_RATIFICATION_COMPLETE",),
        threshold_value_authorized=True,
        threshold_numeric_max_age_seconds=float(RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS),
        owner_threshold_record_digest=threshold_input.owner_threshold_authorization_record_digest,
        threshold_ledger_entry_digest=threshold_result.threshold_ledger_entry_digest,
        configuration_digest_after_threshold=str(cfg_record.get("configuration_digest") or ""),
        scoped_owner_threshold_value_authorized=bool(
            cfg_record.get("scoped_owner_threshold_value_authorized")
        ),
        threshold_value_ratified=bool(cfg_record.get("scoped_owner_threshold_value_authorized")),
        productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
    )
    return GovernedF1M9ThresholdValueRatificationResultV1(
        status="CONTINUATION_COMPLETE",
        decision_code="F1_M9_THRESHOLD_VALUE_RATIFICATION_CONTINUATION_COMPLETE",
        blocking_reasons=(),
        threshold_hot_path_ratified=THRESHOLD_HOT_PATH_RATIFIED,
        exact_value_authority_valid=True,
        f1_m9_value_binding_valid=True,
        real_p4_to_f1_m9_join_status=REAL_P4_TO_F1_M9_JOIN_STATUS,
        productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
        external_effect=EXTERNAL_EFFECT is True,
        ratification_evidence=evidence,
        configuration_digest_after_threshold=str(cfg_record.get("configuration_digest") or ""),
        owner_threshold_record_digest=threshold_input.owner_threshold_authorization_record_digest,
    )


def _reject(reasons: tuple[str, ...]) -> GovernedF1M9ThresholdValueRatificationResultV1:
    evidence = build_threshold_ratification_state_evidence_v1(
        phase_state=F1M9ThresholdRatificationPhaseStateV1.RATIFICATION_DENIED,
        reason_codes=reasons,
        threshold_value_authorized=False,
        threshold_numeric_max_age_seconds=None,
        owner_threshold_record_digest=None,
        threshold_ledger_entry_digest=None,
        configuration_digest_after_threshold=None,
        scoped_owner_threshold_value_authorized=False,
        threshold_value_ratified=False,
        productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
    )
    return GovernedF1M9ThresholdValueRatificationResultV1(
        status="REJECTED",
        decision_code="F1_M9_THRESHOLD_VALUE_RATIFICATION_DENIED",
        blocking_reasons=reasons,
        threshold_hot_path_ratified=False,
        exact_value_authority_valid=False,
        f1_m9_value_binding_valid=False,
        real_p4_to_f1_m9_join_status=REAL_P4_TO_F1_M9_JOIN_STATUS,
        productive_activation_authorized=PRODUCTIVE_ACTIVATION_AUTHORIZED,
        external_effect=EXTERNAL_EFFECT is True,
        ratification_evidence=evidence,
        configuration_digest_after_threshold=None,
        owner_threshold_record_digest=None,
    )


def prove_continuation_authority_invariants_v1() -> bool:
    return (
        PRODUCTIVE_ACTIVATION_AUTHORIZED is False
        and EXTERNAL_EFFECT is False
        and REAL_P4_TO_F1_M9_JOIN_STATUS == JOIN_STATUS_NOT_CANONICAL
        and THRESHOLD_HOT_PATH_RATIFIED is True
    )


def prove_continuation_decision_files_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    paths = (
        DECISION_CONFIG,
        OWNER_WP_DECISION_CONFIG,
        NORMATIVE_SPEC,
        "src/governance/governed_f1_m9_scoped_owner_threshold_value_ratification_real_mechanical_continuation_v1.py",
        "tests/governance/test_governed_f1_m9_scoped_owner_threshold_value_ratification_real_mechanical_continuation_v1.py",
    )
    if not all((root / rel).is_file() for rel in paths):
        return False
    decision = json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))
    return (
        decision.get("workpackage_id") == WORKPACKAGE_ID
        and owner.get("owner_threshold_value_ratification_authorized") is True
        and int(owner.get("threshold_numeric_max_age_seconds"))
        == RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS
        and decision.get("productive_activation_authorized") is False
    )


__all__ = [
    "DECISION_CONFIG",
    "GovernedF1M9ThresholdValueRatificationRequestV1",
    "GovernedF1M9ThresholdValueRatificationResultV1",
    "NORMATIVE_SPEC",
    "OWNER_WP_DECISION_CONFIG",
    "PRODUCTIVE_ACTIVATION_AUTHORIZED",
    "RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS",
    "REAL_P4_TO_F1_M9_JOIN_STATUS",
    "SCHEMA_VERSION",
    "THRESHOLD_HOT_PATH_RATIFIED",
    "WORKPACKAGE_ID",
    "prove_continuation_authority_invariants_v1",
    "prove_continuation_decision_files_v1",
    "run_governed_f1_m9_scoped_owner_threshold_value_ratification_continuation_v1",
]
