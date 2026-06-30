"""
Promotion Economic Gate v1 (RUNBOOK STEP 29N).

Fail-closed, non-authorizing promotion *candidate* eligibility evaluation.
A positive result grants PROMOTION_CANDIDATE_ELIGIBLE only — never deployment,
runtime, activation, or execution authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from src.backtest.economic_validity_policy_v1 import (
    ECONOMIC_VALIDITY_POLICY_VERSION,
    canonical_economic_validity_policy_v1,
)

PROMOTION_ECONOMIC_GATE_POLICY_ID = "promotion_economic_gate"
PROMOTION_ECONOMIC_GATE_POLICY_VERSION = "promotion_economic_gate_v1"
PROMOTION_ECONOMIC_GATE_POLICY_SCHEMA_VERSION = "1"
PROMOTION_ECONOMIC_GATE_POLICY_OWNER = "governance.promotion_loop.promotion_economic_gate_v1"
PROMOTION_ECONOMIC_GATE_POLICY_EFFECTIVE_FROM = "2026-07-01"

AUTHORITY_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"
DEPLOYMENT_EFFECT_NONE = "NONE"
ACTIVATION_EFFECT_NONE = "NONE"

PASS_STATUS = "PASS"
FAIL_STATUS = "FAIL"

PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_DEPLOYMENT = True
PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_RUNTIME = True
PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_ACTIVATION = True
PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_EXECUTION = True

REASON_ECONOMIC_VALIDITY_NOT_PROVEN = "ECONOMIC_VALIDITY_NOT_PROVEN"
REASON_PROFITABILITY_CLAIM_NOT_ALLOWED = "PROFITABILITY_CLAIM_NOT_ALLOWED"
REASON_ECONOMIC_EVIDENCE_MISSING = "ECONOMIC_EVIDENCE_MISSING"
REASON_ECONOMIC_EVIDENCE_INADMISSIBLE = "ECONOMIC_EVIDENCE_INADMISSIBLE"
REASON_DATA_ADMISSIBILITY_FAILED = "DATA_ADMISSIBILITY_FAILED"
REASON_POLICY_THRESHOLD_FAILED = "POLICY_THRESHOLD_FAILED"
REASON_WALK_FORWARD_FAILED = "WALK_FORWARD_FAILED"
REASON_OUT_OF_SAMPLE_FAILED = "OUT_OF_SAMPLE_FAILED"
REASON_MONTE_CARLO_FAILED = "MONTE_CARLO_FAILED"
REASON_STRESS_FAILED = "STRESS_FAILED"
REASON_PARAMETER_SENSITIVITY_FAILED = "PARAMETER_SENSITIVITY_FAILED"
REASON_ROBUSTNESS_FAILED = "ROBUSTNESS_FAILED"
REASON_REPRODUCIBILITY_FAILED = "REPRODUCIBILITY_FAILED"
REASON_DIGEST_BINDING_FAILED = "DIGEST_BINDING_FAILED"
REASON_MANIFEST_BINDING_FAILED = "MANIFEST_BINDING_FAILED"
REASON_SAFETY_POLICY_FAILED = "SAFETY_POLICY_FAILED"
REASON_NON_FUTURES_CANDIDATE = "NON_FUTURES_CANDIDATE"
REASON_BITCOIN_DIRECTION_FORBIDDEN = "BITCOIN_DIRECTION_FORBIDDEN"
REASON_POLICY_VERSION_MISSING = "POLICY_VERSION_MISSING"
REASON_POLICY_DIGEST_MISMATCH = "POLICY_DIGEST_MISMATCH"
REASON_EVIDENCE_DIGEST_MISMATCH = "EVIDENCE_DIGEST_MISMATCH"
REASON_REQUIRED_INPUT_MISSING = "REQUIRED_INPUT_MISSING"
REASON_REQUIRED_STATUS_UNKNOWN = "REQUIRED_STATUS_UNKNOWN"
REASON_NON_FINITE_METRIC = "NON_FINITE_METRIC"
REASON_RUNTIME_AUTHORITY_REQUEST_FORBIDDEN = "RUNTIME_AUTHORITY_REQUEST_FORBIDDEN"
REASON_DEPLOYMENT_ACTIVATION_FORBIDDEN = "DEPLOYMENT_ACTIVATION_FORBIDDEN"

_BLOCKED_REASON_CODES = frozenset(
    {
        REASON_REQUIRED_INPUT_MISSING,
        REASON_REQUIRED_STATUS_UNKNOWN,
        REASON_NON_FINITE_METRIC,
        REASON_POLICY_VERSION_MISSING,
        REASON_POLICY_DIGEST_MISMATCH,
        REASON_EVIDENCE_DIGEST_MISMATCH,
        REASON_DIGEST_BINDING_FAILED,
        REASON_MANIFEST_BINDING_FAILED,
        REASON_ECONOMIC_EVIDENCE_MISSING,
    }
)

_REQUIRED_INPUT_FIELDS = (
    "strategy_id",
    "strategy_version",
    "candidate_id",
    "economic_viability_evidence_ref",
    "economic_validity_status",
    "robustness_status",
    "data_admissibility_status",
    "evidence_admissibility_status",
    "policy_threshold_status",
    "walk_forward_status",
    "out_of_sample_status",
    "monte_carlo_status",
    "stress_status",
    "parameter_sensitivity_status",
    "reproducibility_status",
    "digest_binding_status",
    "manifest_binding_status",
    "safety_policy_status",
    "config_digest",
    "implementation_digest",
    "policy_digest",
    "evidence_manifest_digest",
)

_ROBUSTNESS_STATUS_FIELDS = (
    ("walk_forward_status", REASON_WALK_FORWARD_FAILED),
    ("out_of_sample_status", REASON_OUT_OF_SAMPLE_FAILED),
    ("monte_carlo_status", REASON_MONTE_CARLO_FAILED),
    ("stress_status", REASON_STRESS_FAILED),
    ("parameter_sensitivity_status", REASON_PARAMETER_SENSITIVITY_FAILED),
    ("reproducibility_status", REASON_REPRODUCIBILITY_FAILED),
)


class PromotionCandidateStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    BLOCKED = "BLOCKED"


class PromotionEconomicGateError(ValueError):
    """Fail-closed promotion economic gate error."""


@dataclass(frozen=True)
class PromotionEconomicGatePolicyV1:
    policy_id: str = PROMOTION_ECONOMIC_GATE_POLICY_ID
    policy_version: str = PROMOTION_ECONOMIC_GATE_POLICY_VERSION
    policy_schema_version: str = PROMOTION_ECONOMIC_GATE_POLICY_SCHEMA_VERSION
    owner: str = PROMOTION_ECONOMIC_GATE_POLICY_OWNER
    effective_from: str = PROMOTION_ECONOMIC_GATE_POLICY_EFFECTIVE_FROM
    economic_validity_policy_version: str = ECONOMIC_VALIDITY_POLICY_VERSION
    futures_only: bool = True
    bitcoin_direction_allowed: bool = False
    require_real_admissible_futures_evidence: bool = True
    require_profitability_claim_allowed: bool = True
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = RUNTIME_EFFECT_NONE
    deployment_effect: str = DEPLOYMENT_EFFECT_NONE
    activation_effect: str = ACTIVATION_EFFECT_NONE

    def is_version_bound(self) -> bool:
        return (
            self.policy_id == PROMOTION_ECONOMIC_GATE_POLICY_ID
            and self.policy_version == PROMOTION_ECONOMIC_GATE_POLICY_VERSION
            and self.owner == PROMOTION_ECONOMIC_GATE_POLICY_OWNER
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_schema_version": self.policy_schema_version,
            "owner": self.owner,
            "effective_from": self.effective_from,
            "economic_validity_policy_version": self.economic_validity_policy_version,
            "futures_only": self.futures_only,
            "bitcoin_direction_allowed": self.bitcoin_direction_allowed,
            "require_real_admissible_futures_evidence": self.require_real_admissible_futures_evidence,
            "require_profitability_claim_allowed": self.require_profitability_claim_allowed,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "deployment_effect": self.deployment_effect,
            "activation_effect": self.activation_effect,
        }

    def policy_digest(self) -> str:
        return compute_promotion_economic_gate_policy_digest(self)


@dataclass(frozen=True)
class PromotionEconomicGateInputV1:
    strategy_id: str
    strategy_version: str
    candidate_id: str
    economic_viability_evidence_ref: str
    economic_validity_status: str
    robustness_status: str
    data_admissibility_status: str
    evidence_admissibility_status: str
    policy_threshold_status: str
    walk_forward_status: str
    out_of_sample_status: str
    monte_carlo_status: str
    stress_status: str
    parameter_sensitivity_status: str
    reproducibility_status: str
    digest_binding_status: str
    manifest_binding_status: str
    safety_policy_status: str
    futures_only: bool
    bitcoin_direction_allowed: bool
    config_digest: str
    implementation_digest: str
    policy_digest: str
    evidence_manifest_digest: str
    economic_validity_proven: bool = False
    profitability_claim_allowed: bool = False
    dataset_digest: str = ""
    robustness_result_digests: tuple[str, ...] = ()
    safety_policy_digest: str = ""
    required_metrics: Mapping[str, Optional[float]] = field(default_factory=dict)
    evidence_admissible: Optional[bool] = None
    request_runtime_authority: bool = False
    request_deployment_activation: bool = False

    def to_evaluation_dict(self) -> dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "candidate_id": self.candidate_id,
            "economic_viability_evidence_ref": self.economic_viability_evidence_ref,
            "economic_validity_status": self.economic_validity_status,
            "economic_validity_proven": self.economic_validity_proven,
            "profitability_claim_allowed": self.profitability_claim_allowed,
            "robustness_status": self.robustness_status,
            "data_admissibility_status": self.data_admissibility_status,
            "evidence_admissibility_status": self.evidence_admissibility_status,
            "policy_threshold_status": self.policy_threshold_status,
            "walk_forward_status": self.walk_forward_status,
            "out_of_sample_status": self.out_of_sample_status,
            "monte_carlo_status": self.monte_carlo_status,
            "stress_status": self.stress_status,
            "parameter_sensitivity_status": self.parameter_sensitivity_status,
            "reproducibility_status": self.reproducibility_status,
            "digest_binding_status": self.digest_binding_status,
            "manifest_binding_status": self.manifest_binding_status,
            "safety_policy_status": self.safety_policy_status,
            "futures_only": self.futures_only,
            "bitcoin_direction_allowed": self.bitcoin_direction_allowed,
            "config_digest": self.config_digest,
            "implementation_digest": self.implementation_digest,
            "policy_digest": self.policy_digest,
            "dataset_digest": self.dataset_digest,
            "evidence_manifest_digest": self.evidence_manifest_digest,
            "robustness_result_digests": list(self.robustness_result_digests),
            "safety_policy_digest": self.safety_policy_digest,
            "required_metrics": dict(sorted(self.required_metrics.items())),
            "evidence_admissible": self.evidence_admissible,
            "request_runtime_authority": self.request_runtime_authority,
            "request_deployment_activation": self.request_deployment_activation,
        }


@dataclass(frozen=True)
class PromotionEconomicGateResultV1:
    gate_result_id: str
    gate_policy_id: str
    gate_policy_version: str
    promotion_candidate_status: PromotionCandidateStatus
    eligible_for_promotion_candidate: bool
    blocking_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    evaluated_evidence_refs: tuple[str, ...]
    evaluation_timestamp: str
    evaluation_digest: str
    authority_effect: str
    runtime_effect: str
    deployment_effect: str
    activation_effect: str
    deployment_eligible: bool = False
    runtime_eligible: bool = False
    activation_allowed: bool = False
    execution_allowed: bool = False
    gate_policy_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_result_id": self.gate_result_id,
            "gate_policy_id": self.gate_policy_id,
            "gate_policy_version": self.gate_policy_version,
            "gate_policy_digest": self.gate_policy_digest,
            "promotion_candidate_status": self.promotion_candidate_status.value,
            "eligible_for_promotion_candidate": self.eligible_for_promotion_candidate,
            "blocking_reasons": list(self.blocking_reasons),
            "reason_codes": list(self.reason_codes),
            "evaluated_evidence_refs": list(self.evaluated_evidence_refs),
            "evaluation_timestamp": self.evaluation_timestamp,
            "evaluation_digest": self.evaluation_digest,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "deployment_effect": self.deployment_effect,
            "activation_effect": self.activation_effect,
            "deployment_eligible": self.deployment_eligible,
            "runtime_eligible": self.runtime_eligible,
            "activation_allowed": self.activation_allowed,
            "execution_allowed": self.execution_allowed,
        }


def _stable_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compute_promotion_economic_gate_policy_digest(
    policy: PromotionEconomicGatePolicyV1,
) -> str:
    return _stable_digest(policy.to_dict())


def canonical_promotion_economic_gate_policy_v1() -> PromotionEconomicGatePolicyV1:
    return PromotionEconomicGatePolicyV1()


def validate_promotion_economic_gate_policy_v1(policy: PromotionEconomicGatePolicyV1) -> None:
    if not policy.is_version_bound():
        raise PromotionEconomicGateError("policy_version_not_bound")
    if not policy.policy_version:
        raise PromotionEconomicGateError("policy_version_missing")
    if policy.bitcoin_direction_allowed:
        raise PromotionEconomicGateError("bitcoin_direction_must_be_forbidden")
    if not policy.futures_only:
        raise PromotionEconomicGateError("futures_only_required")


def _normalize_status(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.upper()


def _status_is_pass(value: Any) -> Optional[bool]:
    normalized = _normalize_status(value)
    if normalized is None:
        return None
    if normalized == PASS_STATUS:
        return True
    if normalized in {FAIL_STATUS, "FAILED", "NOT_PROVEN", "INELIGIBLE"}:
        return False
    return None


def _append_missing(field_name: str, reason_codes: list[str]) -> None:
    reason_codes.append(f"{REASON_REQUIRED_INPUT_MISSING}:{field_name}")


def _append_unknown(field_name: str, reason_codes: list[str]) -> None:
    reason_codes.append(f"{REASON_REQUIRED_STATUS_UNKNOWN}:{field_name}")


def _check_status_field(
    *,
    field_name: str,
    value: Any,
    reason_codes: list[str],
    fail_code: str,
) -> None:
    outcome = _status_is_pass(value)
    if outcome is None:
        if value is None or str(value).strip() == "":
            _append_missing(field_name, reason_codes)
        else:
            _append_unknown(field_name, reason_codes)
        return
    if not outcome:
        reason_codes.append(fail_code)


def _check_required_text(field_name: str, value: Any, reason_codes: list[str]) -> None:
    if value is None or str(value).strip() == "":
        _append_missing(field_name, reason_codes)


def _check_required_metrics(
    metrics: Mapping[str, Optional[float]], reason_codes: list[str]
) -> None:
    for field_name, value in sorted(metrics.items()):
        if value is None:
            _append_missing(f"required_metric:{field_name}", reason_codes)
        elif not math.isfinite(float(value)):
            reason_codes.append(f"{REASON_NON_FINITE_METRIC}:{field_name}")


def _derive_robustness_pass(input_data: PromotionEconomicGateInputV1) -> Optional[bool]:
    aggregate = _status_is_pass(input_data.robustness_status)
    component_outcomes = [
        _status_is_pass(getattr(input_data, field_name))
        for field_name, _ in _ROBUSTNESS_STATUS_FIELDS
    ]
    if any(outcome is None for outcome in component_outcomes):
        return None
    components_pass = all(component_outcomes)
    if aggregate is None:
        return components_pass
    return aggregate and components_pass


def compute_promotion_economic_gate_evaluation_digest(
    *,
    policy: PromotionEconomicGatePolicyV1,
    input_data: PromotionEconomicGateInputV1,
) -> str:
    payload = {
        "policy_digest": policy.policy_digest(),
        "input": input_data.to_evaluation_dict(),
    }
    return _stable_digest(payload)


def evaluate_promotion_economic_gate_v1(
    *,
    policy: PromotionEconomicGatePolicyV1,
    input_data: PromotionEconomicGateInputV1,
    evaluation_timestamp: str,
    expected_policy_digest: str = "",
    expected_evidence_manifest_digest: str = "",
) -> PromotionEconomicGateResultV1:
    """Evaluate promotion candidate eligibility against versioned economic gate policy."""
    validate_promotion_economic_gate_policy_v1(policy)
    reason_codes: list[str] = []

    if not policy.policy_version:
        reason_codes.append(REASON_POLICY_VERSION_MISSING)

    for field_name in _REQUIRED_INPUT_FIELDS:
        _check_required_text(field_name, getattr(input_data, field_name), reason_codes)

    if input_data.request_runtime_authority:
        reason_codes.append(REASON_RUNTIME_AUTHORITY_REQUEST_FORBIDDEN)
    if input_data.request_deployment_activation:
        reason_codes.append(REASON_DEPLOYMENT_ACTIVATION_FORBIDDEN)

    if expected_policy_digest and expected_policy_digest != input_data.policy_digest:
        reason_codes.append(REASON_POLICY_DIGEST_MISMATCH)
    if expected_evidence_manifest_digest and (
        expected_evidence_manifest_digest != input_data.evidence_manifest_digest
    ):
        reason_codes.append(REASON_EVIDENCE_DIGEST_MISMATCH)

    _check_status_field(
        field_name="economic_validity_status",
        value=input_data.economic_validity_status,
        reason_codes=reason_codes,
        fail_code=REASON_ECONOMIC_VALIDITY_NOT_PROVEN,
    )
    if input_data.economic_validity_proven is False:
        reason_codes.append(REASON_ECONOMIC_VALIDITY_NOT_PROVEN)
    elif input_data.economic_validity_proven is None:
        _append_unknown("economic_validity_proven", reason_codes)

    if policy.require_profitability_claim_allowed and not input_data.profitability_claim_allowed:
        reason_codes.append(REASON_PROFITABILITY_CLAIM_NOT_ALLOWED)

    if policy.require_real_admissible_futures_evidence:
        if not input_data.economic_viability_evidence_ref.strip():
            reason_codes.append(REASON_ECONOMIC_EVIDENCE_MISSING)
        if input_data.evidence_admissible is False:
            reason_codes.append(REASON_ECONOMIC_EVIDENCE_INADMISSIBLE)
        elif (
            input_data.evidence_admissible is None
            and _status_is_pass(input_data.evidence_admissibility_status) is False
        ):
            reason_codes.append(REASON_ECONOMIC_EVIDENCE_INADMISSIBLE)

    _check_status_field(
        field_name="data_admissibility_status",
        value=input_data.data_admissibility_status,
        reason_codes=reason_codes,
        fail_code=REASON_DATA_ADMISSIBILITY_FAILED,
    )
    _check_status_field(
        field_name="evidence_admissibility_status",
        value=input_data.evidence_admissibility_status,
        reason_codes=reason_codes,
        fail_code=REASON_ECONOMIC_EVIDENCE_INADMISSIBLE,
    )
    _check_status_field(
        field_name="policy_threshold_status",
        value=input_data.policy_threshold_status,
        reason_codes=reason_codes,
        fail_code=REASON_POLICY_THRESHOLD_FAILED,
    )
    for field_name, fail_code in _ROBUSTNESS_STATUS_FIELDS:
        _check_status_field(
            field_name=field_name,
            value=getattr(input_data, field_name),
            reason_codes=reason_codes,
            fail_code=fail_code,
        )

    robustness_pass = _derive_robustness_pass(input_data)
    if robustness_pass is None:
        _append_unknown("robustness_status", reason_codes)
    elif not robustness_pass:
        reason_codes.append(REASON_ROBUSTNESS_FAILED)

    _check_status_field(
        field_name="digest_binding_status",
        value=input_data.digest_binding_status,
        reason_codes=reason_codes,
        fail_code=REASON_DIGEST_BINDING_FAILED,
    )
    _check_status_field(
        field_name="manifest_binding_status",
        value=input_data.manifest_binding_status,
        reason_codes=reason_codes,
        fail_code=REASON_MANIFEST_BINDING_FAILED,
    )
    _check_status_field(
        field_name="safety_policy_status",
        value=input_data.safety_policy_status,
        reason_codes=reason_codes,
        fail_code=REASON_SAFETY_POLICY_FAILED,
    )

    if policy.futures_only and not input_data.futures_only:
        reason_codes.append(REASON_NON_FUTURES_CANDIDATE)
    if input_data.bitcoin_direction_allowed or policy.bitcoin_direction_allowed:
        reason_codes.append(REASON_BITCOIN_DIRECTION_FORBIDDEN)

    _check_required_metrics(input_data.required_metrics, reason_codes)

    unique_reasons = tuple(sorted(set(reason_codes)))
    blocked = any(
        code == blocked_code or code.startswith(f"{blocked_code}:")
        for code in unique_reasons
        for blocked_code in _BLOCKED_REASON_CODES
    )
    if blocked:
        status = PromotionCandidateStatus.BLOCKED
    elif unique_reasons:
        status = PromotionCandidateStatus.INELIGIBLE
    else:
        status = PromotionCandidateStatus.ELIGIBLE

    eligible = status is PromotionCandidateStatus.ELIGIBLE
    evaluation_digest = compute_promotion_economic_gate_evaluation_digest(
        policy=policy,
        input_data=input_data,
    )
    gate_result_id = f"promotion_economic_gate_v1:{evaluation_digest[:16]}"

    evidence_refs: list[str] = []
    if input_data.economic_viability_evidence_ref.strip():
        evidence_refs.append(input_data.economic_viability_evidence_ref.strip())

    return PromotionEconomicGateResultV1(
        gate_result_id=gate_result_id,
        gate_policy_id=policy.policy_id,
        gate_policy_version=policy.policy_version,
        gate_policy_digest=policy.policy_digest(),
        promotion_candidate_status=status,
        eligible_for_promotion_candidate=eligible,
        blocking_reasons=unique_reasons,
        reason_codes=unique_reasons,
        evaluated_evidence_refs=tuple(evidence_refs),
        evaluation_timestamp=evaluation_timestamp,
        evaluation_digest=evaluation_digest,
        authority_effect=AUTHORITY_EFFECT_NONE,
        runtime_effect=RUNTIME_EFFECT_NONE,
        deployment_effect=DEPLOYMENT_EFFECT_NONE,
        activation_effect=ACTIVATION_EFFECT_NONE,
        deployment_eligible=False,
        runtime_eligible=False,
        activation_allowed=False,
        execution_allowed=False,
    )


def evaluate_current_repo_promotion_gate_v1(
    *,
    evaluation_timestamp: str = "2026-07-01T00:00:00Z",
) -> PromotionEconomicGateResultV1:
    """Fail-closed evaluation for the current repo posture (STEP 29N slice)."""
    economic_policy = canonical_economic_validity_policy_v1()
    gate_policy = canonical_promotion_economic_gate_policy_v1()
    input_data = PromotionEconomicGateInputV1(
        strategy_id="mv2_offline_research",
        strategy_version="v1",
        candidate_id="repo_current_state",
        economic_viability_evidence_ref="",
        economic_validity_status=FAIL_STATUS,
        economic_validity_proven=False,
        profitability_claim_allowed=False,
        robustness_status=PASS_STATUS,
        data_admissibility_status=PASS_STATUS,
        evidence_admissibility_status=PASS_STATUS,
        policy_threshold_status=PASS_STATUS,
        walk_forward_status=PASS_STATUS,
        out_of_sample_status=PASS_STATUS,
        monte_carlo_status=PASS_STATUS,
        stress_status=PASS_STATUS,
        parameter_sensitivity_status=PASS_STATUS,
        reproducibility_status=PASS_STATUS,
        digest_binding_status=PASS_STATUS,
        manifest_binding_status=PASS_STATUS,
        safety_policy_status=PASS_STATUS,
        futures_only=True,
        bitcoin_direction_allowed=False,
        config_digest="0" * 64,
        implementation_digest="1" * 64,
        policy_digest=economic_policy.policy_digest(),
        evidence_manifest_digest="2" * 64,
        evidence_admissible=False,
    )
    return evaluate_promotion_economic_gate_v1(
        policy=gate_policy,
        input_data=input_data,
        evaluation_timestamp=evaluation_timestamp,
        expected_policy_digest=economic_policy.policy_digest(),
    )


def promotion_economic_gate_schema_v1() -> dict[str, Any]:
    return {
        "contract_name": "promotion_economic_gate_v1",
        "policy_id": PROMOTION_ECONOMIC_GATE_POLICY_ID,
        "policy_version": PROMOTION_ECONOMIC_GATE_POLICY_VERSION,
        "owner": PROMOTION_ECONOMIC_GATE_POLICY_OWNER,
        "candidate_statuses": [status.value for status in PromotionCandidateStatus],
        "required_input_fields": list(_REQUIRED_INPUT_FIELDS),
        "reason_codes": sorted(
            {
                REASON_ECONOMIC_VALIDITY_NOT_PROVEN,
                REASON_PROFITABILITY_CLAIM_NOT_ALLOWED,
                REASON_ECONOMIC_EVIDENCE_MISSING,
                REASON_ECONOMIC_EVIDENCE_INADMISSIBLE,
                REASON_DATA_ADMISSIBILITY_FAILED,
                REASON_POLICY_THRESHOLD_FAILED,
                REASON_WALK_FORWARD_FAILED,
                REASON_OUT_OF_SAMPLE_FAILED,
                REASON_MONTE_CARLO_FAILED,
                REASON_STRESS_FAILED,
                REASON_PARAMETER_SENSITIVITY_FAILED,
                REASON_ROBUSTNESS_FAILED,
                REASON_REPRODUCIBILITY_FAILED,
                REASON_DIGEST_BINDING_FAILED,
                REASON_MANIFEST_BINDING_FAILED,
                REASON_SAFETY_POLICY_FAILED,
                REASON_NON_FUTURES_CANDIDATE,
                REASON_BITCOIN_DIRECTION_FORBIDDEN,
                REASON_POLICY_VERSION_MISSING,
                REASON_POLICY_DIGEST_MISMATCH,
                REASON_EVIDENCE_DIGEST_MISMATCH,
                REASON_REQUIRED_INPUT_MISSING,
                REASON_REQUIRED_STATUS_UNKNOWN,
                REASON_NON_FINITE_METRIC,
                REASON_RUNTIME_AUTHORITY_REQUEST_FORBIDDEN,
                REASON_DEPLOYMENT_ACTIVATION_FORBIDDEN,
            }
        ),
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "runtime_effect": RUNTIME_EFFECT_NONE,
        "deployment_effect": DEPLOYMENT_EFFECT_NONE,
        "activation_effect": ACTIVATION_EFFECT_NONE,
        "promotion_candidate_eligibility_does_not_imply_deployment": (
            PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_DEPLOYMENT
        ),
        "promotion_candidate_eligibility_does_not_imply_runtime": (
            PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_RUNTIME
        ),
        "promotion_candidate_eligibility_does_not_imply_activation": (
            PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_ACTIVATION
        ),
        "promotion_candidate_eligibility_does_not_imply_execution": (
            PROMOTION_CANDIDATE_ELIGIBILITY_DOES_NOT_IMPLY_EXECUTION
        ),
    }
