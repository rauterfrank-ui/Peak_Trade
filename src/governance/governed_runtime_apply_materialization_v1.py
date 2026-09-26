"""Governed runtime apply materialization ingress, admission, operation, and consumer boundary v1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.governed_runtime_apply_materialization_record_v1 import (
    GovernedRuntimeApplyMaterializationRecordV1,
    RuntimeApplyMaterializationDecisionStateV1,
    build_materialization_record_body_v1,
    compute_lineage_chain_digest_v1,
    verify_materialization_record_digest_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.constants_v1 import (
    SEAM_BIND_DISPOSITION,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "governed_runtime_apply_materialization/v1"
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_P4_L6_SEAM_TO_RUNTIME_APPLY_MATERIALIZATION_REAL_MECHANICAL_CONTINUATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_P4_L6_SEAM_TO_RUNTIME_APPLY_MATERIALIZATION_REAL_MECHANICAL_CONTINUATION_V1.md"
)
OWNER_WP_DECISION_CONFIG: Final[str] = (
    "config/governance/governed_runtime_apply_materialization_wp_v1_owner_decision_v1.json"
)

RUNTIME_APPLY_STARTED: Final[bool] = False
CONFIGURATION_APPLIED: Final[bool] = False
PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
COMPONENT_B_ACTIVATED: Final[bool] = False
PRODUCTIVE_CONFIGURATION_MUTATED: Final[bool] = False
SEAM_BOUND_IMPLIES_PRODUCTIVE_ACTIVATION: Final[bool] = False
SEAM_BOUND_IMPLIES_RUNTIME_APPLY_STARTED: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


class RuntimeApplyMaterializationCallerClassV1(str, Enum):
    GOVERNED_RUNTIME_APPLY_MATERIALIZATION = "GOVERNED_RUNTIME_APPLY_MATERIALIZATION"
    OPTIMIZATION = "OPTIMIZATION"
    META_LEARNING = "META_LEARNING"
    P5_EVIDENCE = "P5_EVIDENCE"
    COMPONENT_B = "COMPONENT_B"


@dataclass(frozen=True, slots=True)
class RuntimeApplyMaterializationIngressV1:
    p4_l6_seam_result_digest: str
    p3_binding_result_digest: str
    component_a_adjudication_digest: str
    optimization_envelope_content_hash: str
    p4_seam_disposition: str
    lineage_chain: tuple[str, ...]
    real_upstream_source_used: bool
    ddo_fixture_state_used: bool


@dataclass(frozen=True, slots=True)
class RuntimeApplyMaterializationEvaluateRequestV1:
    ingress: RuntimeApplyMaterializationIngressV1
    request_materialization_authorization: bool = False
    caller_class: RuntimeApplyMaterializationCallerClassV1 = (
        RuntimeApplyMaterializationCallerClassV1.GOVERNED_RUNTIME_APPLY_MATERIALIZATION
    )


@dataclass(frozen=True, slots=True)
class RuntimeApplyMaterializationEvaluateResultV1:
    decision_state: RuntimeApplyMaterializationDecisionStateV1
    reason_codes: tuple[str, ...]
    materialization_record: GovernedRuntimeApplyMaterializationRecordV1 | None
    runtime_apply_ingress_reached: bool
    runtime_apply_authorization_valid: bool
    configuration_materialized: bool
    configuration_applied: bool
    real_runtime_materialization_performed: bool
    runtime_consumer_boundary_reached: bool
    external_effect_authorized: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration_applied": self.configuration_applied,
            "configuration_materialized": self.configuration_materialized,
            "decision_state": self.decision_state.value,
            "external_effect_authorized": self.external_effect_authorized,
            "materialization_record": (
                self.materialization_record.to_dict() if self.materialization_record else None
            ),
            "real_runtime_materialization_performed": self.real_runtime_materialization_performed,
            "reason_codes": list(self.reason_codes),
            "runtime_apply_authorization_valid": self.runtime_apply_authorization_valid,
            "runtime_apply_ingress_reached": self.runtime_apply_ingress_reached,
            "runtime_consumer_boundary_reached": self.runtime_consumer_boundary_reached,
        }


def _deny(
    reason_codes: list[str],
    *,
    ingress_reached: bool = False,
) -> RuntimeApplyMaterializationEvaluateResultV1:
    return RuntimeApplyMaterializationEvaluateResultV1(
        decision_state=RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_DENIED,
        reason_codes=tuple(reason_codes),
        materialization_record=None,
        runtime_apply_ingress_reached=ingress_reached,
        runtime_apply_authorization_valid=False,
        configuration_materialized=False,
        configuration_applied=False,
        real_runtime_materialization_performed=False,
        runtime_consumer_boundary_reached=False,
        external_effect_authorized=False,
    )


def _digest_from_lineage_v1(*, prefix: str, lineage_chain: tuple[str, ...]) -> str | None:
    needle = f"{prefix}://"
    for ref in lineage_chain:
        if ref.startswith(needle):
            digest = ref[len(needle) :]
            if is_valid_sha256_hex(digest):
                return digest
    return None


def validate_runtime_apply_materialization_ingress_v1(
    ingress: RuntimeApplyMaterializationIngressV1,
) -> list[str]:
    reasons: list[str] = []
    if ingress.ddo_fixture_state_used:
        reasons.append("DDO_FIXTURE_STATE_FORBIDDEN_ON_RUNTIME_APPLY_INGRESS")
    if not ingress.real_upstream_source_used:
        reasons.append("REAL_UPSTREAM_SOURCE_REQUIRED")
    if ingress.p4_seam_disposition != SEAM_BIND_DISPOSITION:
        reasons.append("P4_L6_SEAM_NOT_BOUND")
    for field_name, value in (
        ("P4_L6_SEAM_RESULT_DIGEST", ingress.p4_l6_seam_result_digest),
        ("P3_BINDING_RESULT_DIGEST", ingress.p3_binding_result_digest),
        ("COMPONENT_A_ADJUDICATION_DIGEST", ingress.component_a_adjudication_digest),
        ("OPTIMIZATION_ENVELOPE_CONTENT_HASH", ingress.optimization_envelope_content_hash),
    ):
        if not is_valid_sha256_hex(value):
            reasons.append(f"{field_name}_INVALID")
    chain_p4 = _digest_from_lineage_v1(prefix="p4_l6_seam", lineage_chain=ingress.lineage_chain)
    chain_p3 = _digest_from_lineage_v1(prefix="p3_binding", lineage_chain=ingress.lineage_chain)
    chain_adj = _digest_from_lineage_v1(
        prefix="adjudicator_a_opt", lineage_chain=ingress.lineage_chain
    )
    chain_env = _digest_from_lineage_v1(
        prefix="optimization_envelope", lineage_chain=ingress.lineage_chain
    )
    if chain_p4 != ingress.p4_l6_seam_result_digest:
        reasons.append("P4_L6_SEAM_LINEAGE_MISMATCH")
    if chain_p3 != ingress.p3_binding_result_digest:
        reasons.append("P3_BINDING_LINEAGE_MISMATCH")
    if chain_adj != ingress.component_a_adjudication_digest:
        reasons.append("COMPONENT_A_ADJUDICATION_LINEAGE_MISMATCH")
    if chain_env != ingress.optimization_envelope_content_hash:
        reasons.append("OPTIMIZATION_ENVELOPE_LINEAGE_MISMATCH")
    expected_env_ref = f"optimization_envelope://{ingress.optimization_envelope_content_hash}"
    if expected_env_ref not in ingress.lineage_chain:
        reasons.append("OPTIMIZATION_ENVELOPE_LINEAGE_MISSING")
    return reasons


def load_runtime_apply_wp_owner_decision_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or _REPO_ROOT
    return json.loads((root / OWNER_WP_DECISION_CONFIG).read_text(encoding="utf-8"))


def validate_runtime_apply_materialization_admission_v1(
    *,
    owner_decision: Mapping[str, Any],
    request_materialization_authorization: bool,
) -> list[str]:
    reasons: list[str] = []
    if owner_decision.get("runtime_apply_wp_authorized") is not True:
        reasons.append("RUNTIME_APPLY_WP_NOT_OWNER_AUTHORIZED")
    if owner_decision.get("productive_activation_authorized") is True:
        reasons.append("PRODUCTIVE_ACTIVATION_FORBIDDEN_IN_WP_DECISION")
    if owner_decision.get("external_effect_authorized") is True:
        reasons.append("EXTERNAL_EFFECT_FORBIDDEN_IN_WP_DECISION")
    if owner_decision.get("component_b_activated") is True:
        reasons.append("COMPONENT_B_ACTIVATION_FORBIDDEN_IN_WP_DECISION")
    if (
        request_materialization_authorization
        and owner_decision.get("materialization_authorization_permitted") is not True
    ):
        reasons.append("MATERIALIZATION_AUTHORIZATION_NOT_PERMITTED_BY_OWNER")
    return reasons


def _validate_caller_class_v1(caller: RuntimeApplyMaterializationCallerClassV1) -> list[str]:
    if caller == RuntimeApplyMaterializationCallerClassV1.GOVERNED_RUNTIME_APPLY_MATERIALIZATION:
        return []
    if caller == RuntimeApplyMaterializationCallerClassV1.OPTIMIZATION:
        return ["OPTIMIZATION_CANNOT_INVOKE_RUNTIME_APPLY_MATERIALIZATION"]
    if caller == RuntimeApplyMaterializationCallerClassV1.META_LEARNING:
        return ["META_LEARNING_CANNOT_INVOKE_RUNTIME_APPLY_MATERIALIZATION"]
    if caller == RuntimeApplyMaterializationCallerClassV1.P5_EVIDENCE:
        return ["P5_EVIDENCE_CANNOT_INVOKE_RUNTIME_APPLY_MATERIALIZATION"]
    if caller == RuntimeApplyMaterializationCallerClassV1.COMPONENT_B:
        return ["COMPONENT_B_CANNOT_INVOKE_RUNTIME_APPLY_MATERIALIZATION"]
    return ["RUNTIME_APPLY_CALLER_CLASS_FORBIDDEN"]


def evaluate_runtime_apply_materialization_v1(
    request: RuntimeApplyMaterializationEvaluateRequestV1,
    *,
    repo_root: Path | None = None,
) -> RuntimeApplyMaterializationEvaluateResultV1:
    """Fail-closed runtime apply materialization through typed record only."""
    reason_codes: list[str] = []
    reason_codes.extend(_validate_caller_class_v1(request.caller_class))
    ingress_reasons = validate_runtime_apply_materialization_ingress_v1(request.ingress)
    ingress_reached = not ingress_reasons
    reason_codes.extend(ingress_reasons)

    owner = load_runtime_apply_wp_owner_decision_v1(repo_root=repo_root)
    reason_codes.extend(
        validate_runtime_apply_materialization_admission_v1(
            owner_decision=owner,
            request_materialization_authorization=request.request_materialization_authorization,
        )
    )
    if reason_codes:
        return _deny(reason_codes, ingress_reached=ingress_reached)

    ingress = request.ingress
    lineage_digest = compute_lineage_chain_digest_v1(lineage_chain=ingress.lineage_chain)
    decision_state = (
        RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_AUTHORIZED
        if request.request_materialization_authorization
        else RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_ELIGIBLE
    )
    reason_ok = (
        "MATERIALIZATION_AUTHORIZED_NO_PRODUCTIVE_APPLY"
        if request.request_materialization_authorization
        else "MATERIALIZATION_ELIGIBLE_BOUNDARY_OK"
    )
    record_body = build_materialization_record_body_v1(
        decision_state=decision_state,
        p4_l6_seam_result_digest=ingress.p4_l6_seam_result_digest,
        p3_binding_result_digest=ingress.p3_binding_result_digest,
        component_a_adjudication_digest=ingress.component_a_adjudication_digest,
        optimization_envelope_content_hash=ingress.optimization_envelope_content_hash,
        lineage_chain_digest=lineage_digest,
        reason_codes=(reason_ok,),
        real_runtime_materialization_performed=True,
    )
    if not verify_materialization_record_digest_v1(record_body):
        return _deny(["MATERIALIZATION_RECORD_DIGEST_INVALID"], ingress_reached=True)

    record = GovernedRuntimeApplyMaterializationRecordV1(
        materialization_record=record_body,
        materialization_record_digest=str(record_body["materialization_record_digest"]),
        decision_state=decision_state,
    )
    consumer = evaluate_runtime_apply_consumer_boundary_v1(record)
    if consumer.reason_codes:
        return _deny(list(consumer.reason_codes), ingress_reached=True)

    return RuntimeApplyMaterializationEvaluateResultV1(
        decision_state=decision_state,
        reason_codes=(decision_state.value,),
        materialization_record=record,
        runtime_apply_ingress_reached=True,
        runtime_apply_authorization_valid=True,
        configuration_materialized=True,
        configuration_applied=False,
        real_runtime_materialization_performed=True,
        runtime_consumer_boundary_reached=True,
        external_effect_authorized=False,
    )


@dataclass(frozen=True, slots=True)
class RuntimeApplyConsumerBoundaryResultV1:
    reason_codes: tuple[str, ...]
    post_allowed: bool
    wire_send_permitted: bool
    real_venue_post_allowed: bool
    credential_access_performed: bool
    autonomy_can_mint_permit: bool
    autonomy_can_post: bool


def evaluate_runtime_apply_consumer_boundary_v1(
    record: GovernedRuntimeApplyMaterializationRecordV1,
) -> RuntimeApplyConsumerBoundaryResultV1:
    """Runtime consumer stops before productive activation and external effect."""
    reasons: list[str] = []
    body = record.materialization_record
    if body.get("configuration_applied") is True:
        reasons.append("CONFIGURATION_APPLIED_FORBIDDEN_IN_WP")
    if body.get("runtime_apply_started") is True:
        reasons.append("RUNTIME_APPLY_STARTED_FORBIDDEN_IN_WP")
    if body.get("productive_activation_authorized") is True:
        reasons.append("PRODUCTIVE_ACTIVATION_INFERENCE_FORBIDDEN")
    if body.get("external_effect_authorized") is True:
        reasons.append("EXTERNAL_EFFECT_INFERENCE_FORBIDDEN")
    if record.decision_state == RuntimeApplyMaterializationDecisionStateV1.MATERIALIZATION_APPLIED:
        reasons.append("MATERIALIZATION_APPLIED_STATE_FORBIDDEN")
    return RuntimeApplyConsumerBoundaryResultV1(
        reason_codes=tuple(reasons),
        post_allowed=False,
        wire_send_permitted=False,
        real_venue_post_allowed=False,
        credential_access_performed=False,
        autonomy_can_mint_permit=False,
        autonomy_can_post=False,
    )


def seam_bound_implies_productive_activation_v1() -> bool:
    return False


def materialization_implies_configuration_applied_v1() -> bool:
    return False


def prove_negative_runtime_apply_materialization_safety_invariants_v1() -> bool:
    checks = (
        RUNTIME_APPLY_STARTED is False,
        CONFIGURATION_APPLIED is False,
        PRODUCTIVE_ACTIVATION_AUTHORIZED is False,
        EXTERNAL_EFFECT_AUTHORIZED is False,
        COMPONENT_B_ACTIVATED is False,
        PRODUCTIVE_CONFIGURATION_MUTATED is False,
        SEAM_BOUND_IMPLIES_PRODUCTIVE_ACTIVATION is False,
        SEAM_BOUND_IMPLIES_RUNTIME_APPLY_STARTED is False,
        seam_bound_implies_productive_activation_v1() is False,
        materialization_implies_configuration_applied_v1() is False,
    )
    return all(checks)


__all__ = [
    "COMPONENT_B_ACTIVATED",
    "CONFIGURATION_APPLIED",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "NORMATIVE_SPEC",
    "OWNER_WP_DECISION_CONFIG",
    "PRODUCTIVE_ACTIVATION_AUTHORIZED",
    "PRODUCTIVE_CONFIGURATION_MUTATED",
    "RUNTIME_APPLY_STARTED",
    "RuntimeApplyConsumerBoundaryResultV1",
    "RuntimeApplyMaterializationCallerClassV1",
    "RuntimeApplyMaterializationEvaluateRequestV1",
    "RuntimeApplyMaterializationEvaluateResultV1",
    "RuntimeApplyMaterializationIngressV1",
    "SCHEMA_VERSION",
    "SEAM_BOUND_IMPLIES_PRODUCTIVE_ACTIVATION",
    "SEAM_BOUND_IMPLIES_RUNTIME_APPLY_STARTED",
    "WORKPACKAGE_ID",
    "evaluate_runtime_apply_consumer_boundary_v1",
    "evaluate_runtime_apply_materialization_v1",
    "load_runtime_apply_wp_owner_decision_v1",
    "materialization_implies_configuration_applied_v1",
    "prove_negative_runtime_apply_materialization_safety_invariants_v1",
    "seam_bound_implies_productive_activation_v1",
    "validate_runtime_apply_materialization_admission_v1",
    "validate_runtime_apply_materialization_ingress_v1",
]
