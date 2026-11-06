"""Offline productive linear diagnostics promotion economic gate consumer binding v0.

Narrow adapter: consumes PR #5186 economic evidence consumer binding and evaluates
the canonical promotion_economic_gate_v1 owner fail-closed. Diagnostic-only —
no economic evaluation, promotion authority, or runtime effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.governance.promotion_loop.promotion_economic_gate_v1 import (
    AUTHORITY_EFFECT_NONE,
    FAIL_STATUS,
    PASS_STATUS,
    PROMOTION_ECONOMIC_GATE_POLICY_OWNER,
    PromotionCandidateStatus,
    PromotionEconomicGateInputV1,
    PromotionEconomicGateResultV1,
    canonical_promotion_economic_gate_policy_v1,
    evaluate_promotion_economic_gate_v1,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0 import (
    CONSUMER_BINDING_OWNER as ECONOMIC_EVIDENCE_CONSUMER_BINDING_OWNER,
    EconomicEvidenceAdmissibility,
    LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
    materialize_linear_diagnostics_economic_evidence_consumer_binding_v0,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    SourceBundleSpecV0,
    SupportAggregateStatus,
)

PROMOTION_CONSUMER_BINDING_SCHEMA_VERSION = (
    "offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding.v0"
)
PROMOTION_CONSUMER_BINDING_EVIDENCE_TYPE = (
    "OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_PROMOTION_ECONOMIC_GATE_CONSUMER_BINDING_V0"
)
PROMOTION_CONSUMER_BINDING_OWNER = (
    "research.linear_evidence."
    "offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0"
)
CANONICAL_PROMOTION_GATE_OWNER = PROMOTION_ECONOMIC_GATE_POLICY_OWNER
ECONOMIC_EVIDENCE_CONSUMER_SOURCE = ECONOMIC_EVIDENCE_CONSUMER_BINDING_OWNER

DEFAULT_STRATEGY_ID = "offline_productive_linear_diagnostics"
DEFAULT_STRATEGY_VERSION = "v0"
DEFAULT_CANDIDATE_ID = "pr5186_linear_diagnostics_consumer_bound_input"
DEFAULT_EVALUATION_TIMESTAMP = "2026-07-14T23:16:52Z"

BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT = "BLOCKED_SOURCE_DIAGNOSTICS_PRESENT"
BLOCKING_REASON_RANK_DEFICIENT_BLOCKED = "RANK_DEFICIENT_BLOCKED"
BLOCKING_REASON_BLOCK_DRIFT_EXCEEDS_POLICY = "BLOCK_DRIFT_EXCEEDS_POLICY"
BLOCKING_REASON_LINEAR_DIAGNOSTICS_MISSING = "LINEAR_DIAGNOSTICS_CONSUMER_BINDING_MISSING"
BLOCKING_REASON_LINEAR_DIAGNOSTICS_INCONSISTENT = "LINEAR_DIAGNOSTICS_AGGREGATE_INCONSISTENT"


class PromotionEconomicGateConsumerBindingError(ValueError):
    """Fail-closed promotion economic gate consumer binding error."""


class PromotionEconomicGateBindingStatus(str, Enum):
    BLOCKED = "BLOCKED"
    INELIGIBLE = "INELIGIBLE"
    ELIGIBLE = "ELIGIBLE"


@dataclass(frozen=True)
class PromotionEconomicGateConsumerBindingContextV0:
    strategy_id: str
    strategy_version: str
    candidate_id: str
    config_digest: str
    implementation_digest: str
    evidence_manifest_digest: str
    economic_viability_evidence_ref: str = ""


@dataclass(frozen=True)
class PromotionEconomicGateConsumerBindingResultV0:
    schema_version: str
    owner: str
    canonical_promotion_gate_owner: str
    economic_evidence_consumer_source: str
    promotion_economic_gate_status: str
    promotion_candidate_eligible: bool
    evidence_admissible: bool
    blocking_reason: tuple[str, ...]
    linear_diagnostics_status: str
    linear_diagnostics_reason_codes: tuple[str, ...]
    economic_evidence_admissibility: str
    cost_diagnostics_status: str
    signal_orthogonality_status: str
    factor_exposure_status: str
    parameter_sensitivity_status: str
    rolling_linear_drift_status: str
    aggregate_status: str
    gate_result: PromotionEconomicGateResultV1
    economic_evaluation_executed: bool
    economic_validity_pass_created: bool
    promotion_pass_created: bool
    runtime_effect: str
    authority_effect: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "owner": self.owner,
            "canonical_promotion_gate_owner": self.canonical_promotion_gate_owner,
            "economic_evidence_consumer_source": self.economic_evidence_consumer_source,
            "promotion_economic_gate_status": self.promotion_economic_gate_status,
            "promotion_candidate_eligible": self.promotion_candidate_eligible,
            "evidence_admissible": self.evidence_admissible,
            "blocking_reason": list(self.blocking_reason),
            "linear_diagnostics_status": self.linear_diagnostics_status,
            "linear_diagnostics_reason_codes": list(self.linear_diagnostics_reason_codes),
            "economic_evidence_admissibility": self.economic_evidence_admissibility,
            "cost_diagnostics_status": self.cost_diagnostics_status,
            "signal_orthogonality_status": self.signal_orthogonality_status,
            "factor_exposure_status": self.factor_exposure_status,
            "parameter_sensitivity_status": self.parameter_sensitivity_status,
            "rolling_linear_drift_status": self.rolling_linear_drift_status,
            "aggregate_status": self.aggregate_status,
            "gate_result": self.gate_result.to_dict(),
            "economic_evaluation_executed": self.economic_evaluation_executed,
            "economic_validity_pass_created": self.economic_validity_pass_created,
            "promotion_pass_created": self.promotion_pass_created,
            "runtime_effect": self.runtime_effect,
            "authority_effect": self.authority_effect,
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _normalize_reason_codes(reasons: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(item) for item in reasons if str(item)}))


def _digest_suffix(value: str) -> str:
    text = str(value).strip()
    if len(text) >= 64:
        return text[:64]
    return _stable_digest({"value": text})


def default_promotion_consumer_binding_context_v0(
    consumer_binding: LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
) -> PromotionEconomicGateConsumerBindingContextV0:
    bundle_digest = consumer_binding.support_bundle_output_digest
    return PromotionEconomicGateConsumerBindingContextV0(
        strategy_id=DEFAULT_STRATEGY_ID,
        strategy_version=DEFAULT_STRATEGY_VERSION,
        candidate_id=DEFAULT_CANDIDATE_ID,
        config_digest=_digest_suffix(f"config:{bundle_digest}"),
        implementation_digest=_digest_suffix(f"implementation:{bundle_digest}"),
        evidence_manifest_digest=_digest_suffix(bundle_digest),
        economic_viability_evidence_ref=(
            f"research/linear_diagnostics_consumer_binding/{bundle_digest[:16]}"
        ),
    )


def map_evidence_admissibility_to_promotion_gate_v0(
    economic_evidence_admissibility: str,
) -> tuple[bool, str]:
    normalized = str(economic_evidence_admissibility).strip()
    if normalized == EconomicEvidenceAdmissibility.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value:
        return True, PASS_STATUS
    if normalized in {
        EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value,
        EconomicEvidenceAdmissibility.WARN_SOURCE_DIAGNOSTICS_PRESENT.value,
        EconomicEvidenceAdmissibility.INSUFFICIENT_SOURCE_BINDING.value,
        EconomicEvidenceAdmissibility.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value,
    }:
        return False, FAIL_STATUS
    return False, FAIL_STATUS


def derive_linear_diagnostics_promotion_blocking_reasons_v0(
    consumer_binding: LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
) -> tuple[str, ...]:
    reasons: list[str] = []
    admissibility = consumer_binding.economic_evidence_admissibility
    if admissibility == EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value:
        reasons.append(BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT)
    if consumer_binding.cost_diagnostics_status == "RANK_DEFICIENT_BLOCKED":
        reasons.append(BLOCKING_REASON_RANK_DEFICIENT_BLOCKED)
    if consumer_binding.factor_exposure_status == "RANK_DEFICIENT_BLOCKED":
        reasons.append(BLOCKING_REASON_RANK_DEFICIENT_BLOCKED)
    if consumer_binding.rolling_linear_drift_status == "BLOCK_DRIFT_EXCEEDS_POLICY":
        reasons.append(BLOCKING_REASON_BLOCK_DRIFT_EXCEEDS_POLICY)
    reasons.extend(consumer_binding.linear_diagnostics_reason_codes)
    if consumer_binding.aggregate_status == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value:
        reasons.append(consumer_binding.aggregate_status)
    return _normalize_reason_codes(reasons)


def _assert_consumer_binding_consistent_v0(
    consumer_binding: LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
) -> None:
    if consumer_binding.aggregate_status == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value:
        if (
            consumer_binding.economic_evidence_admissibility
            == EconomicEvidenceAdmissibility.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value
        ):
            raise PromotionEconomicGateConsumerBindingError(
                BLOCKING_REASON_LINEAR_DIAGNOSTICS_INCONSISTENT
            )
    if consumer_binding.economic_viability_support_status == "BLOCKED_SOURCE_DIAGNOSTICS_PRESENT":
        if (
            consumer_binding.economic_evidence_admissibility
            != EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
        ):
            raise PromotionEconomicGateConsumerBindingError(
                BLOCKING_REASON_LINEAR_DIAGNOSTICS_INCONSISTENT
            )


def build_promotion_gate_input_from_linear_diagnostics_consumer_binding_v0(
    *,
    ctx: PromotionEconomicGateConsumerBindingContextV0,
    consumer_binding: LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
) -> PromotionEconomicGateInputV1:
    _assert_consumer_binding_consistent_v0(consumer_binding)
    evidence_admissible, evidence_admissibility_status = (
        map_evidence_admissibility_to_promotion_gate_v0(
            consumer_binding.economic_evidence_admissibility
        )
    )
    economic_policy = canonical_economic_validity_policy_v1()
    evidence_ref = ctx.economic_viability_evidence_ref.strip()
    if not evidence_ref:
        evidence_ref = (
            f"research/linear_diagnostics_consumer_binding/"
            f"{consumer_binding.support_bundle_output_digest[:16]}"
        )
    return PromotionEconomicGateInputV1(
        strategy_id=ctx.strategy_id,
        strategy_version=ctx.strategy_version,
        candidate_id=ctx.candidate_id,
        economic_viability_evidence_ref=evidence_ref,
        economic_validity_status=FAIL_STATUS,
        economic_validity_proven=False,
        profitability_claim_allowed=False,
        economic_validity_offline_gate_pass=False,
        robustness_status=FAIL_STATUS,
        data_admissibility_status=PASS_STATUS,
        evidence_admissibility_status=evidence_admissibility_status,
        evidence_admissible=evidence_admissible,
        policy_threshold_status=FAIL_STATUS,
        walk_forward_status=FAIL_STATUS,
        out_of_sample_status=FAIL_STATUS,
        monte_carlo_status=FAIL_STATUS,
        stress_status=FAIL_STATUS,
        parameter_sensitivity_status=consumer_binding.parameter_sensitivity_status,
        reproducibility_status=PASS_STATUS,
        digest_binding_status=PASS_STATUS,
        manifest_binding_status=PASS_STATUS,
        safety_policy_status=PASS_STATUS,
        futures_only=True,
        bitcoin_direction_allowed=False,
        config_digest=ctx.config_digest,
        implementation_digest=ctx.implementation_digest,
        policy_digest=economic_policy.policy_digest(),
        evidence_manifest_digest=ctx.evidence_manifest_digest,
    )


def _promotion_gate_status_from_result(
    gate_result: PromotionEconomicGateResultV1,
) -> PromotionEconomicGateBindingStatus:
    if gate_result.promotion_candidate_status is PromotionCandidateStatus.BLOCKED:
        return PromotionEconomicGateBindingStatus.BLOCKED
    if gate_result.promotion_candidate_status is PromotionCandidateStatus.ELIGIBLE:
        return PromotionEconomicGateBindingStatus.ELIGIBLE
    return PromotionEconomicGateBindingStatus.INELIGIBLE


def evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
    *,
    consumer_binding: LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
    ctx: PromotionEconomicGateConsumerBindingContextV0 | None = None,
    evaluation_timestamp: str = DEFAULT_EVALUATION_TIMESTAMP,
) -> PromotionEconomicGateConsumerBindingResultV0:
    binding_ctx = ctx or default_promotion_consumer_binding_context_v0(consumer_binding)
    gate_input = build_promotion_gate_input_from_linear_diagnostics_consumer_binding_v0(
        ctx=binding_ctx,
        consumer_binding=consumer_binding,
    )
    gate_policy = canonical_promotion_economic_gate_policy_v1()
    gate_result = evaluate_promotion_economic_gate_v1(
        policy=gate_policy,
        input_data=gate_input,
        evaluation_timestamp=evaluation_timestamp,
        expected_policy_digest=gate_input.policy_digest,
    )
    linear_blocking = derive_linear_diagnostics_promotion_blocking_reasons_v0(consumer_binding)
    gate_reasons = tuple(gate_result.reason_codes)
    blocking_reason = _normalize_reason_codes([*gate_reasons, *linear_blocking])
    gate_status = _promotion_gate_status_from_result(gate_result)
    eligible = gate_result.eligible_for_promotion_candidate and not linear_blocking
    if linear_blocking and gate_status is PromotionEconomicGateBindingStatus.ELIGIBLE:
        gate_status = PromotionEconomicGateBindingStatus.INELIGIBLE
        eligible = False
    if (
        consumer_binding.economic_evidence_admissibility
        != EconomicEvidenceAdmissibility.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value
    ):
        eligible = False
        if gate_status is PromotionEconomicGateBindingStatus.ELIGIBLE:
            gate_status = PromotionEconomicGateBindingStatus.INELIGIBLE
    if consumer_binding.aggregate_status == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value:
        eligible = False
        if gate_status is not PromotionEconomicGateBindingStatus.BLOCKED:
            gate_status = PromotionEconomicGateBindingStatus.BLOCKED
    return PromotionEconomicGateConsumerBindingResultV0(
        schema_version=PROMOTION_CONSUMER_BINDING_SCHEMA_VERSION,
        owner=PROMOTION_CONSUMER_BINDING_OWNER,
        canonical_promotion_gate_owner=CANONICAL_PROMOTION_GATE_OWNER,
        economic_evidence_consumer_source=ECONOMIC_EVIDENCE_CONSUMER_SOURCE,
        promotion_economic_gate_status=gate_status.value,
        promotion_candidate_eligible=eligible,
        evidence_admissible=gate_result.evidence_admissible,
        blocking_reason=blocking_reason,
        linear_diagnostics_status=consumer_binding.linear_diagnostics_status,
        linear_diagnostics_reason_codes=consumer_binding.linear_diagnostics_reason_codes,
        economic_evidence_admissibility=consumer_binding.economic_evidence_admissibility,
        cost_diagnostics_status=consumer_binding.cost_diagnostics_status,
        signal_orthogonality_status=consumer_binding.signal_orthogonality_status,
        factor_exposure_status=consumer_binding.factor_exposure_status,
        parameter_sensitivity_status=consumer_binding.parameter_sensitivity_status,
        rolling_linear_drift_status=consumer_binding.rolling_linear_drift_status,
        aggregate_status=consumer_binding.aggregate_status,
        gate_result=gate_result,
        economic_evaluation_executed=False,
        economic_validity_pass_created=False,
        promotion_pass_created=False,
        runtime_effect=RUNTIME_EFFECT,
        authority_effect=AUTHORITY_EFFECT,
    )


def materialize_promotion_economic_gate_consumer_binding_v0(
    *,
    source_specs: Sequence[SourceBundleSpecV0],
    verify_fn: Callable[[Path], tuple[bool, str]],
    repo_root: Path | None = None,
    ctx: PromotionEconomicGateConsumerBindingContextV0 | None = None,
    evaluation_timestamp: str = DEFAULT_EVALUATION_TIMESTAMP,
) -> tuple[
    dict[str, Any],
    LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
    PromotionEconomicGateConsumerBindingResultV0,
]:
    support_bundle, consumer_binding = (
        materialize_linear_diagnostics_economic_evidence_consumer_binding_v0(
            source_specs=source_specs,
            verify_fn=verify_fn,
            repo_root=repo_root,
        )
    )
    promotion_result = evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
        consumer_binding=consumer_binding,
        ctx=ctx,
        evaluation_timestamp=evaluation_timestamp,
    )
    return support_bundle, consumer_binding, promotion_result


def promotion_gate_binding_matrix_v0() -> dict[str, Any]:
    return {
        "canonical_promotion_gate_owner": CANONICAL_PROMOTION_GATE_OWNER,
        "economic_evidence_consumer_source": ECONOMIC_EVIDENCE_CONSUMER_SOURCE,
        "promotion_gate_callable": (
            "governance.promotion_loop.promotion_economic_gate_v1.evaluate_promotion_economic_gate_v1"
        ),
        "required_consumer_fields": [
            "economic_evidence_admissibility",
            "linear_diagnostics_status",
            "linear_diagnostics_reason_codes",
            "aggregate_status",
            "cost_diagnostics_status",
            "signal_orthogonality_status",
            "factor_exposure_status",
            "parameter_sensitivity_status",
            "rolling_linear_drift_status",
            "support_bundle_output_digest",
        ],
        "promotion_input_fail_closed_defaults": {
            "economic_validity_status": FAIL_STATUS,
            "economic_validity_proven": False,
            "robustness_status": FAIL_STATUS,
            "walk_forward_status": FAIL_STATUS,
            "out_of_sample_status": FAIL_STATUS,
            "monte_carlo_status": FAIL_STATUS,
            "stress_status": FAIL_STATUS,
            "policy_threshold_status": FAIL_STATUS,
        },
        "linear_diagnostics_cannot_create": [
            "economic_validity_pass",
            "promotion_pass",
            "shadow_pass",
            "runtime_rewire_pass",
        ],
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "runtime_effect": RUNTIME_EFFECT,
    }


def status_reason_mapping_v0() -> dict[str, Any]:
    return {
        "economic_evidence_admissibility_to_promotion": {
            EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value: {
                "evidence_admissible": False,
                "promotion_blocking_reason": BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
            },
            EconomicEvidenceAdmissibility.WARN_SOURCE_DIAGNOSTICS_PRESENT.value: {
                "evidence_admissible": False,
                "promotion_blocking_reason": "WARN_SOURCE_DIAGNOSTICS_PRESENT",
            },
            EconomicEvidenceAdmissibility.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value: {
                "evidence_admissible": True,
                "promotion_blocking_reason": None,
            },
        },
        "source_status_blocking_codes": {
            "RANK_DEFICIENT_BLOCKED": BLOCKING_REASON_RANK_DEFICIENT_BLOCKED,
            "BLOCK_DRIFT_EXCEEDS_POLICY": BLOCKING_REASON_BLOCK_DRIFT_EXCEEDS_POLICY,
        },
        "positive_classes_do_not_override_aggregate_block": [
            "OK",
            "ROBUST_REGION_OBSERVED",
        ],
        "missing_or_unknown_fail_closed": True,
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT",
    "BLOCKING_REASON_BLOCK_DRIFT_EXCEEDS_POLICY",
    "BLOCKING_REASON_LINEAR_DIAGNOSTICS_INCONSISTENT",
    "BLOCKING_REASON_LINEAR_DIAGNOSTICS_MISSING",
    "BLOCKING_REASON_RANK_DEFICIENT_BLOCKED",
    "CANONICAL_PROMOTION_GATE_OWNER",
    "DEFAULT_CANDIDATE_ID",
    "DEFAULT_EVALUATION_TIMESTAMP",
    "DEFAULT_STRATEGY_ID",
    "DEFAULT_STRATEGY_VERSION",
    "ECONOMIC_EVIDENCE_CONSUMER_SOURCE",
    "PROMOTION_CONSUMER_BINDING_EVIDENCE_TYPE",
    "PROMOTION_CONSUMER_BINDING_OWNER",
    "PROMOTION_CONSUMER_BINDING_SCHEMA_VERSION",
    "PromotionEconomicGateBindingStatus",
    "PromotionEconomicGateConsumerBindingContextV0",
    "PromotionEconomicGateConsumerBindingError",
    "PromotionEconomicGateConsumerBindingResultV0",
    "RUNTIME_EFFECT",
    "build_promotion_gate_input_from_linear_diagnostics_consumer_binding_v0",
    "default_promotion_consumer_binding_context_v0",
    "derive_linear_diagnostics_promotion_blocking_reasons_v0",
    "evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0",
    "map_evidence_admissibility_to_promotion_gate_v0",
    "materialize_promotion_economic_gate_consumer_binding_v0",
    "promotion_gate_binding_matrix_v0",
    "status_reason_mapping_v0",
]
