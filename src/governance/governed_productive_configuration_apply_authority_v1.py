"""Governed productive configuration apply authority v1 (Owner-ratified; no runtime apply).

Adjudicates apply eligibility and bounded apply authorization from an M10 authorized
promotion record into a typed materialization-contract apply record only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_M9_SURFACE_ID,
)
from src.governance.authorized_productive_parameter_seam_v1 import (
    SEAM_OWNER,
    STATUS_BOUND as SEAM_STATUS_BOUND,
    AuthorizedProductiveParameterSeamResultV1,
)
from src.governance.governed_productive_configuration_apply_record_v1 import (
    APPLY_AUTHORITY_ID,
    APPLY_RECORD_SCHEMA_VERSION,
    GovernedProductiveConfigurationApplyRecordV1,
    ProductiveConfigurationApplyDecisionStateV1,
    build_apply_record_body_v1,
    compute_evidence_lineage_digest_ref_v1,
    compute_repository_provenance_digest_v1,
    verify_apply_record_digest_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    SCHEMA_VERSION as CONFIGURATION_SCHEMA_VERSION,
    STATUS_MATERIALIZED,
    GovernedProductiveConfigurationResultV1,
    verify_configuration_record_digest_v1,
)
from src.governance.m10_promotion_boundary_v1 import (
    AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
    AUTHORIZED_PROMOTION_RECORD_SCHEMA_VERSION,
    M10PromotionState,
    verify_m10_authorized_promotion_record_digest_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    POLICY_CONSUMER_MODULE,
    POLICY_EVALUATOR_SYMBOL,
    PRODUCTIVE_TARGET_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    validate_optimization_proposal_governance_ingress_v1,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    TRADING_DECISION_AUTHORITY_OWNER,
)

SCHEMA_VERSION: Final[str] = "governed_productive_configuration_apply_authority/v1"
WORKPACKAGE_ID: Final[str] = "GOVERNED_RUNTIME_APPLY_MATERIALIZATION_AUTHORITY_RATIFICATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/GOVERNED_PRODUCTIVE_CONFIGURATION_APPLY_AUTHORITY_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/governed_productive_configuration_apply_authority_v1_decision_v1.json"
)
OWNER_RATIFICATION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_runtime_apply_materialization_authority_ratification_v1_owner_decision_v1.json"
)

RATIFIED_PRODUCTIVE_APPLY_SURFACE_IDS: Final[frozenset[str]] = frozenset({F1_M9_SURFACE_ID})

RUNTIME_APPLY_STARTED: Final[bool] = False
REAL_RUNTIME_MATERIALIZATION_PERFORMED: Final[bool] = False
PRODUCTIVE_CONFIGURATION_MUTATED: Final[bool] = False
PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
M11_STARTED: Final[bool] = False

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
META_LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
TRADING_SELECTION_EFFECT: Final[str] = "NONE"
TRADING_DECISION_AUTHORITY_CHANGE: Final[str] = "NONE"
RISK_AUTHORITY_CHANGE: Final[str] = "NONE"

P5_EVIDENCE_INTAKE_IMPLIES_APPLY: Final[bool] = False
PRIMARY_EVIDENCE_IMPLIES_APPLY: Final[bool] = False
EXPERIMENT_EVIDENCE_IMPLIES_APPLY: Final[bool] = False

PRODUCTIVE_PARAMETER_SEAM_OWNER_REF: Final[str] = SEAM_OWNER

_REPO_ROOT = Path(__file__).resolve().parents[2]


class ApplyAuthorityCallerClassV1(str, Enum):
    GOVERNED_APPLY_AUTHORITY = "GOVERNED_APPLY_AUTHORITY"
    OPTIMIZATION = "OPTIMIZATION"
    META_LEARNING = "META_LEARNING"
    P5_EVIDENCE = "P5_EVIDENCE"
    PRIMARY_RUNTIME_EVIDENCE = "PRIMARY_RUNTIME_EVIDENCE"
    EXPERIMENT_EVIDENCE = "EXPERIMENT_EVIDENCE"
    M10_PROMOTION_ONLY = "M10_PROMOTION_ONLY"


@dataclass(frozen=True, slots=True)
class GovernedProductiveConfigurationApplyEvaluateRequestV1:
    authorized_promotion_record: Mapping[str, Any]
    ingress: Mapping[str, Any]
    configuration: GovernedProductiveConfigurationResultV1
    seam: AuthorizedProductiveParameterSeamResultV1
    request_apply_authorization: bool = False
    caller_class: ApplyAuthorityCallerClassV1 = ApplyAuthorityCallerClassV1.GOVERNED_APPLY_AUTHORITY


@dataclass(frozen=True, slots=True)
class GovernedProductiveConfigurationApplyEvaluateResultV1:
    decision_state: ProductiveConfigurationApplyDecisionStateV1
    reason_codes: tuple[str, ...]
    apply_record: GovernedProductiveConfigurationApplyRecordV1 | None
    trading_decision_authority_owner: str
    external_effect_authorized: bool
    runtime_apply_started: bool
    runtime_materialization_performed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_record": self.apply_record.to_dict() if self.apply_record else None,
            "decision_state": self.decision_state.value,
            "external_effect_authorized": self.external_effect_authorized,
            "reason_codes": list(self.reason_codes),
            "runtime_apply_started": self.runtime_apply_started,
            "runtime_materialization_performed": self.runtime_materialization_performed,
            "trading_decision_authority_owner": self.trading_decision_authority_owner,
        }


def _deny(reason_codes: list[str]) -> GovernedProductiveConfigurationApplyEvaluateResultV1:
    return GovernedProductiveConfigurationApplyEvaluateResultV1(
        decision_state=ProductiveConfigurationApplyDecisionStateV1.APPLY_DENIED,
        reason_codes=tuple(reason_codes),
        apply_record=None,
        trading_decision_authority_owner=TRADING_DECISION_AUTHORITY_OWNER,
        external_effect_authorized=False,
        runtime_apply_started=False,
        runtime_materialization_performed=False,
    )


def _validate_caller_class_v1(caller: ApplyAuthorityCallerClassV1) -> list[str]:
    if caller == ApplyAuthorityCallerClassV1.GOVERNED_APPLY_AUTHORITY:
        return []
    if caller == ApplyAuthorityCallerClassV1.OPTIMIZATION:
        return ["OPTIMIZATION_CANNOT_INVOKE_APPLY_AUTHORITY"]
    if caller == ApplyAuthorityCallerClassV1.META_LEARNING:
        return ["META_LEARNING_CANNOT_INVOKE_APPLY_AUTHORITY"]
    if caller == ApplyAuthorityCallerClassV1.P5_EVIDENCE:
        return ["P5_EVIDENCE_INTAKE_CANNOT_INVOKE_APPLY_AUTHORITY"]
    if caller == ApplyAuthorityCallerClassV1.PRIMARY_RUNTIME_EVIDENCE:
        return ["PRIMARY_RUNTIME_EVIDENCE_CANNOT_INVOKE_APPLY_AUTHORITY"]
    if caller == ApplyAuthorityCallerClassV1.EXPERIMENT_EVIDENCE:
        return ["EXPERIMENT_EVIDENCE_CANNOT_INVOKE_APPLY_AUTHORITY"]
    if caller == ApplyAuthorityCallerClassV1.M10_PROMOTION_ONLY:
        return ["M10_AUTHORIZATION_ALONE_INSUFFICIENT_FOR_APPLY"]
    return ["APPLY_CALLER_CLASS_FORBIDDEN"]


def _validate_promotion_record_contract_v1(record: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if record.get("schema_version") != AUTHORIZED_PROMOTION_RECORD_SCHEMA_VERSION:
        reasons.append("M10_AUTHORIZED_RECORD_SCHEMA_MISMATCH")
    if record.get("promotion_state") != M10PromotionState.AUTHORIZED.value:
        reasons.append("M10_PROMOTION_STATE_NOT_AUTHORIZED")
    if not verify_m10_authorized_promotion_record_digest_v1(record):
        reasons.append("M10_AUTHORIZED_RECORD_DIGEST_INVALID")
    if record.get("runtime_apply_authorized") is True:
        reasons.append("M10_RUNTIME_APPLY_FLAG_MUST_BE_FALSE")
    if record.get("productive_configuration_write_authorized") is True:
        reasons.append("M10_PRODUCTIVE_CONFIGURATION_WRITE_FORBIDDEN")
    if record.get("external_effect_authorized") is True:
        reasons.append("M10_EXTERNAL_EFFECT_FORBIDDEN")
    surface_id = str(record.get("surface_id") or "")
    if surface_id not in RATIFIED_PRODUCTIVE_APPLY_SURFACE_IDS:
        if surface_id in (F2_SURFACE_ID, F5_FRESH_SURFACE_ID):
            reasons.append("UNSUPPORTED_SURFACE_RESEARCH_OR_SHADOW_ONLY")
        else:
            reasons.append("UNSUPPORTED_UNRATIFIED_SURFACE")
    return reasons


def _validate_lineage_bindings_v1(
    *,
    promotion: Mapping[str, Any],
    ingress: Mapping[str, Any],
    configuration: GovernedProductiveConfigurationResultV1,
    seam: AuthorizedProductiveParameterSeamResultV1,
) -> list[str]:
    reasons: list[str] = []
    if configuration.configuration_status != STATUS_MATERIALIZED:
        reasons.append("CONFIGURATION_NOT_MATERIALIZED")
    config_record = configuration.configuration_record
    if config_record is None:
        reasons.append("CONFIGURATION_RECORD_MISSING")
        return reasons
    if not verify_configuration_record_digest_v1(dict(config_record)):
        reasons.append("CONFIGURATION_DIGEST_INVALID")

    if seam.seam_status != SEAM_STATUS_BOUND or seam.seam_record is None:
        reasons.append("PRODUCTIVE_SEAM_NOT_BOUND")
        return reasons

    seam_record = seam.seam_record
    seam_digest = str(seam.seam_digest or "")
    if not is_valid_sha256_hex(seam_digest):
        reasons.append("PRODUCTIVE_SEAM_DIGEST_INVALID")

    try:
        validated_ingress = validate_optimization_proposal_governance_ingress_v1(ingress)
    except Exception as exc:
        reasons.append(str(exc))
        validated_ingress = None

    promotion_ingress = str(promotion.get("ingress_digest") or "")
    if not is_valid_sha256_hex(promotion_ingress):
        reasons.append("PROMOTION_INGRESS_DIGEST_INVALID")
    config_ingress = str(config_record.get("ingress_digest") or "")
    if promotion_ingress != config_ingress:
        reasons.append("PROMOTION_CONFIGURATION_INGRESS_MISMATCH")

    if validated_ingress is not None:
        if str(validated_ingress["ingress_digest"]) != promotion_ingress:
            reasons.append("INGRESS_PROMOTION_MISMATCH")
        if str(validated_ingress["candidate_ref"]) != str(promotion.get("candidate_ref") or ""):
            reasons.append("CANDIDATE_ID_MISMATCH")
        expected_candidate_digest = str(promotion.get("candidate_parameter_value_digest") or "")
        config_candidate_digest = str(config_record.get("candidate_parameter_value_digest") or "")
        if expected_candidate_digest != config_candidate_digest:
            reasons.append("AUTHORIZED_VALUE_MISMATCH")
        config_evidence_hash = str(config_record.get("optimization_evidence_content_hash") or "")
        if config_evidence_hash != str(validated_ingress["optimization_evidence_content_hash"]):
            reasons.append("EVIDENCE_LINEAGE_MISMATCH")

    if str(promotion.get("surface_id") or "") != str(
        config_record.get("optimization_surface_id") or ""
    ):
        reasons.append("SURFACE_MISMATCH")
    if str(promotion.get("productive_target_id") or "") != str(
        config_record.get("productive_target_id") or ""
    ):
        reasons.append("TARGET_MISMATCH")
    if promotion.get("productive_target_id") != PRODUCTIVE_TARGET_ID:
        reasons.append("PRODUCTIVE_TARGET_NOT_F1_M9")
    if str(config_record.get("optimization_surface_id") or "") != OPTIMIZATION_SURFACE_ID:
        reasons.append("CONFIGURATION_SURFACE_NOT_F1_M9")

    owner_digest = str(promotion.get("owner_authorization_record_digest") or "")
    if owner_digest != str(config_record.get("owner_authorization_record_digest") or ""):
        reasons.append("OWNER_AUTHORIZATION_MISMATCH")
    explicit_digest = str(promotion.get("explicit_authorization_digest") or "")
    if explicit_digest != str(config_record.get("authorization_digest") or ""):
        reasons.append("EXPLICIT_AUTHORIZATION_MISMATCH")

    config_digest = str(config_record.get("configuration_digest") or "")
    if config_digest != str(seam_record.get("configuration_digest") or ""):
        reasons.append("PRODUCTIVE_SEAM_CONFIGURATION_MISMATCH")

    consumer_module = str(promotion.get("current_consumer_module") or "")
    if not consumer_module:
        reasons.append("PRODUCTIVE_CONSUMER_REF_MISSING")
    seam_consumer = str(seam_record.get("policy_consumer_module") or "")
    if seam_consumer != POLICY_CONSUMER_MODULE:
        reasons.append("PRODUCTIVE_SEAM_CONSUMER_MISMATCH")

    expected_evidence = compute_evidence_lineage_digest_ref_v1(
        lineage_digest=str(promotion.get("lineage_digest") or ""),
        ingress_digest=promotion_ingress,
        explicit_authorization_digest=explicit_digest,
        owner_authorization_record_digest=owner_digest,
    )
    if not is_valid_sha256_hex(expected_evidence):
        reasons.append("EVIDENCE_LINEAGE_DIGEST_INVALID")

    repo_digest = compute_repository_provenance_digest_v1(configuration_record=dict(config_record))
    if not is_valid_sha256_hex(repo_digest):
        reasons.append("REPOSITORY_PROVENANCE_DIGEST_INVALID")

    seam_ref = str(seam_record.get("seam_id") or "")
    if seam_ref != str(seam.seam_record.get("seam_id") or ""):
        reasons.append("PRODUCTIVE_SEAM_REF_MISMATCH")

    return reasons


def evaluate_governed_productive_configuration_apply_v1(
    request: GovernedProductiveConfigurationApplyEvaluateRequestV1,
) -> GovernedProductiveConfigurationApplyEvaluateResultV1:
    """Fail-closed apply eligibility/authorization without runtime materialization."""
    reason_codes: list[str] = []
    reason_codes.extend(_validate_caller_class_v1(request.caller_class))
    reason_codes.extend(_validate_promotion_record_contract_v1(request.authorized_promotion_record))
    reason_codes.extend(
        _validate_lineage_bindings_v1(
            promotion=request.authorized_promotion_record,
            ingress=request.ingress,
            configuration=request.configuration,
            seam=request.seam,
        )
    )

    if reason_codes:
        return _deny(reason_codes)

    promotion = request.authorized_promotion_record
    config_record = request.configuration.configuration_record
    seam_record = request.seam.seam_record
    assert config_record is not None and seam_record is not None

    promotion_digest = str(promotion["authorized_promotion_record_digest"])
    config_digest = str(config_record["configuration_digest"])
    materialization_target_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"materialization-target:{promotion_digest}:{config_digest}",
        )
    )
    governance_risk_ref = str(
        config_record.get("governance_risk_constraints_ref")
        or config_record.get("risk_constraints_ref")
        or ""
    )
    if not governance_risk_ref:
        return _deny(["GOVERNANCE_RISK_AUTHORIZATION_REF_MISSING"])

    evidence_lineage_digest = compute_evidence_lineage_digest_ref_v1(
        lineage_digest=str(promotion.get("lineage_digest") or ""),
        ingress_digest=str(promotion.get("ingress_digest") or ""),
        explicit_authorization_digest=str(promotion.get("explicit_authorization_digest") or ""),
        owner_authorization_record_digest=str(
            promotion.get("owner_authorization_record_digest") or ""
        ),
    )
    repository_provenance_digest = compute_repository_provenance_digest_v1(
        configuration_record=dict(config_record)
    )
    promotion_consumer_module = str(promotion.get("current_consumer_module") or "")
    productive_consumer_ref = (
        f"{promotion_consumer_module}::{POLICY_CONSUMER_MODULE}::{POLICY_EVALUATOR_SYMBOL}"
    )

    if not request.request_apply_authorization:
        record_body = build_apply_record_body_v1(
            decision_state=ProductiveConfigurationApplyDecisionStateV1.APPLY_ELIGIBLE,
            promotion_authorization_id=str(promotion["authorized_promotion_record_id"]),
            authorized_promotion_record_digest=promotion_digest,
            candidate_id=str(promotion["candidate_ref"]),
            surface_id=str(promotion["surface_id"]),
            target_id=str(promotion["productive_target_id"]),
            authorized_candidate_parameter_value_digest=str(
                promotion["candidate_parameter_value_digest"]
            ),
            evidence_lineage_digest=evidence_lineage_digest,
            governance_risk_authorization_ref=governance_risk_ref,
            productive_parameter_seam_ref=str(seam_record["seam_id"]),
            productive_consumer_ref=productive_consumer_ref,
            source_configuration_id=str(config_record["configuration_id"]),
            source_configuration_digest=config_digest,
            materialization_target_configuration_schema_version=CONFIGURATION_SCHEMA_VERSION,
            materialization_target_configuration_id=materialization_target_id,
            repository_provenance_digest=repository_provenance_digest,
            reason_codes=("APPLY_ELIGIBLE_BOUNDARY_OK",),
        )
        if not verify_apply_record_digest_v1(record_body):
            return _deny(["APPLY_RECORD_DIGEST_INVALID"])
        apply_record = GovernedProductiveConfigurationApplyRecordV1(
            apply_record=record_body,
            apply_record_digest=str(record_body["apply_record_digest"]),
            decision_state=ProductiveConfigurationApplyDecisionStateV1.APPLY_ELIGIBLE,
        )
        return GovernedProductiveConfigurationApplyEvaluateResultV1(
            decision_state=ProductiveConfigurationApplyDecisionStateV1.APPLY_ELIGIBLE,
            reason_codes=("APPLY_ELIGIBLE",),
            apply_record=apply_record,
            trading_decision_authority_owner=TRADING_DECISION_AUTHORITY_OWNER,
            external_effect_authorized=False,
            runtime_apply_started=False,
            runtime_materialization_performed=False,
        )

    record_body = build_apply_record_body_v1(
        decision_state=ProductiveConfigurationApplyDecisionStateV1.APPLY_AUTHORIZED,
        promotion_authorization_id=str(promotion["authorized_promotion_record_id"]),
        authorized_promotion_record_digest=promotion_digest,
        candidate_id=str(promotion["candidate_ref"]),
        surface_id=str(promotion["surface_id"]),
        target_id=str(promotion["productive_target_id"]),
        authorized_candidate_parameter_value_digest=str(
            promotion["candidate_parameter_value_digest"]
        ),
        evidence_lineage_digest=evidence_lineage_digest,
        governance_risk_authorization_ref=governance_risk_ref,
        productive_parameter_seam_ref=str(seam_record["seam_id"]),
        productive_consumer_ref=productive_consumer_ref,
        source_configuration_id=str(config_record["configuration_id"]),
        source_configuration_digest=config_digest,
        materialization_target_configuration_schema_version=CONFIGURATION_SCHEMA_VERSION,
        materialization_target_configuration_id=materialization_target_id,
        repository_provenance_digest=repository_provenance_digest,
        reason_codes=("APPLY_AUTHORIZED_NO_RUNTIME_MUTATION",),
    )
    if not verify_apply_record_digest_v1(record_body):
        return _deny(["APPLY_RECORD_DIGEST_INVALID"])
    apply_record = GovernedProductiveConfigurationApplyRecordV1(
        apply_record=MappingProxyType(dict(record_body)),
        apply_record_digest=str(record_body["apply_record_digest"]),
        decision_state=ProductiveConfigurationApplyDecisionStateV1.APPLY_AUTHORIZED,
    )
    return GovernedProductiveConfigurationApplyEvaluateResultV1(
        decision_state=ProductiveConfigurationApplyDecisionStateV1.APPLY_AUTHORIZED,
        reason_codes=("APPLY_AUTHORIZED",),
        apply_record=apply_record,
        trading_decision_authority_owner=TRADING_DECISION_AUTHORITY_OWNER,
        external_effect_authorized=False,
        runtime_apply_started=False,
        runtime_materialization_performed=False,
    )


def optimization_can_invoke_apply_authority_v1() -> bool:
    return False


def meta_learning_can_invoke_apply_authority_v1() -> bool:
    return False


def p5_evidence_intake_implies_apply_authorization_v1() -> bool:
    return False


def primary_runtime_evidence_implies_apply_authorization_v1() -> bool:
    return False


def experiment_evidence_implies_apply_authorization_v1() -> bool:
    return False


def m10_authorization_alone_produces_applied_state_v1() -> bool:
    return False


def apply_authorization_implies_external_effect_v1() -> bool:
    return False


def prove_negative_apply_authority_safety_invariants_v1() -> bool:
    checks = (
        AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is False,
        RUNTIME_APPLY_STARTED is False,
        REAL_RUNTIME_MATERIALIZATION_PERFORMED is False,
        PRODUCTIVE_CONFIGURATION_MUTATED is False,
        PRODUCTIVE_ACTIVATION_AUTHORIZED is False,
        EXTERNAL_EFFECT_AUTHORIZED is False,
        M11_STARTED is False,
        OPTIMIZATION_PRODUCTIVE_AUTHORITY == "NONE",
        META_LEARNING_PRODUCTIVE_AUTHORITY == "NONE",
        TRADING_SELECTION_EFFECT == "NONE",
        TRADING_DECISION_AUTHORITY_CHANGE == "NONE",
        RISK_AUTHORITY_CHANGE == "NONE",
        P5_EVIDENCE_INTAKE_IMPLIES_APPLY is False,
        PRIMARY_EVIDENCE_IMPLIES_APPLY is False,
        EXPERIMENT_EVIDENCE_IMPLIES_APPLY is False,
        optimization_can_invoke_apply_authority_v1() is False,
        meta_learning_can_invoke_apply_authority_v1() is False,
        p5_evidence_intake_implies_apply_authorization_v1() is False,
        primary_runtime_evidence_implies_apply_authorization_v1() is False,
        experiment_evidence_implies_apply_authorization_v1() is False,
        m10_authorization_alone_produces_applied_state_v1() is False,
        apply_authorization_implies_external_effect_v1() is False,
    )
    return all(checks)


__all__ = [
    "APPLY_AUTHORITY_ID",
    "APPLY_RECORD_SCHEMA_VERSION",
    "AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY",
    "ApplyAuthorityCallerClassV1",
    "DECISION_CONFIG",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "GovernedProductiveConfigurationApplyEvaluateRequestV1",
    "GovernedProductiveConfigurationApplyEvaluateResultV1",
    "M11_STARTED",
    "NORMATIVE_SPEC",
    "OPTIMIZATION_PRODUCTIVE_AUTHORITY",
    "OWNER_RATIFICATION_CONFIG",
    "PRODUCTIVE_CONFIGURATION_MUTATED",
    "RATIFIED_PRODUCTIVE_APPLY_SURFACE_IDS",
    "RUNTIME_APPLY_STARTED",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "apply_authorization_implies_external_effect_v1",
    "evaluate_governed_productive_configuration_apply_v1",
    "experiment_evidence_implies_apply_authorization_v1",
    "m10_authorization_alone_produces_applied_state_v1",
    "meta_learning_can_invoke_apply_authority_v1",
    "optimization_can_invoke_apply_authority_v1",
    "p5_evidence_intake_implies_apply_authorization_v1",
    "primary_runtime_evidence_implies_apply_authorization_v1",
    "prove_negative_apply_authority_safety_invariants_v1",
]
