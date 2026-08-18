"""Phase 9 Canonical Portfolio Learning v1 (research evidence only).

Evaluates a research portfolio separately from isolated strategy quality.
Comparability is delegated to Phase 5 Comparison SSOT. A strong single
strategy is never an automatic portfolio component. This layer does not
apply allocations, mutate runtime, write config, promote, fund, or submit
orders.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_comparison_ssot_v1 import (
    COMPARISON_CONTRACT_VERSION,
    CanonicalComparisonRequestV1,
    ComparisonCandidateV1,
    ComparisonCompatibilityContractV1,
    OVERALL_COMPARABLE,
    SCHEMA_VERSION as COMPARISON_SSOT_VERSION,
    build_canonical_comparison_result_v1,
    canonical_record_payload,
)
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityError,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import (
    ARTIFACT_KIND_REPO_RELATIVE,
    ARTIFACT_KIND_STORE_RELATIVE,
    derive_experiment_id_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_portfolio_learning_v1"
PORTFOLIO_LEARNING_DOMAIN: Final[str] = "peak_trade.canonical_portfolio_learning.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
EVIDENCE_KIND_EXPERIMENT_RECORD: Final[str] = "EXPERIMENT_RECORD"
ARTIFACT_KIND_REPO_RELATIVE_REF: Final[str] = ARTIFACT_KIND_REPO_RELATIVE
ARTIFACT_KIND_STORE_RELATIVE_REF: Final[str] = ARTIFACT_KIND_STORE_RELATIVE
EVALUATION_POLICY_VERSION: Final[str] = "canonical_portfolio_learning_policy_v1"
METRIC_DEFINITION_VERSION: Final[str] = "canonical_robustness_metrics_v1"
ROBUSTNESS_SUITE_VERSION: Final[str] = "canonical_robustness_suite_v1"
WEIGHT_SUM_ABS_TOLERANCE: Final[float] = 1e-12

PORTFOLIO_LEARNING_PRESENT: Final[bool] = True
STRATEGY_AND_PORTFOLIO_OPTIMIZATION_SEPARATED: Final[bool] = True
STRONG_SINGLE_STRATEGY_IS_NOT_AUTOMATIC_PORTFOLIO_COMPONENT: Final[bool] = True
AUTONOMOUS_ALLOCATION_APPLY: Final[bool] = False
AUTONOMOUS_PORTFOLIO_PROMOTION: Final[bool] = False
PORTFOLIO_LEARNING_HAS_RUNTIME_AUTHORITY: Final[bool] = False
PORTFOLIO_LEARNING_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
PORTFOLIO_LEARNING_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
PORTFOLIO_LEARNING_CAN_PROMOTE: Final[bool] = False
PORTFOLIO_LEARNING_CAN_PROMOTE_TO_LIVE: Final[bool] = False
PORTFOLIO_LEARNING_CAN_INCREASE_RISK: Final[bool] = False
PORTFOLIO_LEARNING_CAN_INCREASE_LEVERAGE: Final[bool] = False
PORTFOLIO_LEARNING_CAN_FUND: Final[bool] = False
PORTFOLIO_LEARNING_CAN_SUBMIT_ORDER: Final[bool] = False
PORTFOLIO_LEARNING_CAN_ARM: Final[bool] = False
PORTFOLIO_LEARNING_CAN_ENABLE: Final[bool] = False
PORTFOLIO_LEARNING_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
PORTFOLIO_LEARNING_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
PORTFOLIO_LEARNING_CAN_AUTHORIZE_CANARY: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

LAYER_PORTFOLIO: Final[str] = "PORTFOLIO_LAYER"
STATUS_OBSERVED: Final[str] = "STRATEGY_LAYER_OBSERVED"
STATUS_ELIGIBLE: Final[str] = "PORTFOLIO_COMPONENT_ELIGIBLE"
STATUS_INELIGIBLE: Final[str] = "PORTFOLIO_COMPONENT_INELIGIBLE"
DISPOSITION_ELIGIBLE: Final[str] = "PORTFOLIO_ELIGIBLE"
DISPOSITION_INELIGIBLE: Final[str] = "PORTFOLIO_INELIGIBLE"
DISPOSITION_REJECTED_COMPARABILITY: Final[str] = "REJECTED_COMPARABILITY"
EVALUATION_COMPLETE: Final[str] = "EVALUATION_COMPLETE"
EVALUATION_REJECTED: Final[str] = "EVALUATION_REJECTED"

STRATEGY_LAYER_FIELDS: Final[tuple[str, ...]] = (
    "signal_quality",
    "execution_robustness",
    "parameter_stability",
    "regime_suitability",
)

_CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_UNAVAILABLE_TOKENS = frozenset(
    {
        "",
        "unknown",
        "unavailable",
        "n/a",
        "na",
        "none",
        "null",
        "implicit",
        "default",
        "compatible",
        "zero",
    }
)
_EVIDENCE_KINDS: Final[tuple[str, ...]] = (
    EVIDENCE_KIND_EXPERIMENT_RECORD,
    ARTIFACT_KIND_REPO_RELATIVE_REF,
    ARTIFACT_KIND_STORE_RELATIVE_REF,
)

_LOGGER = logging.getLogger(__name__)


class PortfolioLearningValidationError(ValueError):
    """Fail-closed Canonical Portfolio Learning v1 validation error."""


@dataclass(frozen=True)
class StrategyLayerObservationV1:
    signal_quality: float
    execution_robustness: float
    parameter_stability: float
    regime_suitability: float


@dataclass(frozen=True)
class PortfolioMemberV1:
    candidate: ComparisonCandidateV1
    weight: float
    strategy_layer: StrategyLayerObservationV1
    marginal_risk: float
    risk_contribution: float
    fee_drag: float
    slippage: float


@dataclass(frozen=True)
class PairwiseObservationV1:
    left_experiment_id: str
    right_experiment_id: str
    correlation: float
    covariance: float


@dataclass(frozen=True)
class PortfolioPolicyV1:
    max_pairwise_abs_correlation: float
    max_concentration: float
    min_diversification: float
    max_abs_portfolio_drawdown: float
    max_turnover: float
    min_capacity: float
    min_allocation_stability: float
    max_risk_contribution: float
    evaluation_policy_version: str = EVALUATION_POLICY_VERSION


@dataclass(frozen=True)
class CanonicalPortfolioLearningRequestV1:
    members: Sequence[PortfolioMemberV1]
    pairwise: Sequence[PairwiseObservationV1]
    diversification: float
    concentration: float
    portfolio_drawdown: float
    turnover: float
    capacity: float
    allocation_stability: float
    policy: PortfolioPolicyV1
    evidence_refs: Sequence[Mapping[str, Any]]
    created_at: str
    metric_definitions: str = METRIC_DEFINITION_VERSION
    robustness_suite_version: str = ROBUSTNESS_SUITE_VERSION
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None


def build_canonical_portfolio_learning_v1(
    request: CanonicalPortfolioLearningRequestV1,
) -> Mapping[str, Any]:
    created_at = _require_created_at(request.created_at)
    metric_definitions = _require_token("metric_definitions", request.metric_definitions)
    if metric_definitions != METRIC_DEFINITION_VERSION:
        raise PortfolioLearningValidationError("metric_definitions must reuse the Phase 4 token")
    robustness_suite_version = _require_token(
        "robustness_suite_version", request.robustness_suite_version
    )
    if robustness_suite_version != ROBUSTNESS_SUITE_VERSION:
        raise PortfolioLearningValidationError(
            "robustness_suite_version must reuse the Phase 4 token"
        )
    policy = _canonicalize_policy(request.policy)
    bound_members = _canonicalize_members(request.members)
    experiment_ids = [item["experiment_id"] for item in bound_members]
    pairwise_results = _canonicalize_pairwise(
        request.pairwise, experiment_ids, request.compatibility_contract, created_at, bound_members
    )
    comparable = all(
        item["overall_comparability"] == OVERALL_COMPARABLE for item in pairwise_results
    )
    portfolio_metrics = _canonicalize_portfolio_metrics(
        diversification=request.diversification,
        concentration=request.concentration,
        portfolio_drawdown=request.portfolio_drawdown,
        turnover=request.turnover,
        capacity=request.capacity,
        allocation_stability=request.allocation_stability,
        max_weight=max(item["weight"] for item in bound_members),
    )
    if comparable:
        gate_failures = _evaluate_portfolio_gates(
            bound_members=bound_members,
            pairwise_results=pairwise_results,
            portfolio_metrics=portfolio_metrics,
            policy=policy,
        )
        overall_disposition = DISPOSITION_ELIGIBLE if not gate_failures else DISPOSITION_INELIGIBLE
        overall_status = EVALUATION_COMPLETE
        component_status = STATUS_ELIGIBLE if not gate_failures else STATUS_INELIGIBLE
    else:
        overall_disposition = DISPOSITION_REJECTED_COMPARABILITY
        overall_status = EVALUATION_REJECTED
        component_status = DISPOSITION_REJECTED_COMPARABILITY
        gate_failures = ["REJECTED_COMPARABILITY"]
    member_results = [
        {
            "experiment_id": item["experiment_id"],
            "fee_drag": item["fee_drag"],
            "layer": LAYER_PORTFOLIO,
            "marginal_risk": item["marginal_risk"],
            "portfolio_component_status": component_status,
            "risk_contribution": item["risk_contribution"],
            "slippage": item["slippage"],
            "strategy_layer": item["strategy_layer"],
            "strategy_layer_status": STATUS_OBSERVED,
            "weight": item["weight"],
        }
        for item in bound_members
    ]
    evidence_refs = _canonicalize_evidence_refs(request.evidence_refs, experiment_ids)
    body = {
        "applied_allocation": False,
        "autonomous_allocation_apply": AUTONOMOUS_ALLOCATION_APPLY,
        "autonomous_portfolio_promotion": AUTONOMOUS_PORTFOLIO_PROMOTION,
        "comparison_contract_version": COMPARISON_CONTRACT_VERSION,
        "comparison_ssot_version": COMPARISON_SSOT_VERSION,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "evaluation_policy": policy,
        "evidence_refs": evidence_refs,
        "gate_failures": gate_failures,
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "member_experiment_ids": experiment_ids,
        "member_results": member_results,
        "metric_definitions": metric_definitions,
        "overall_disposition": overall_disposition,
        "overall_status": overall_status,
        "pairwise_results": pairwise_results,
        "portfolio_learning_can_arm": PORTFOLIO_LEARNING_CAN_ARM,
        "portfolio_learning_can_authorize_canary": PORTFOLIO_LEARNING_CAN_AUTHORIZE_CANARY,
        "portfolio_learning_can_create_confirm_token": (
            PORTFOLIO_LEARNING_CAN_CREATE_CONFIRM_TOKEN
        ),
        "portfolio_learning_can_enable": PORTFOLIO_LEARNING_CAN_ENABLE,
        "portfolio_learning_can_fund": PORTFOLIO_LEARNING_CAN_FUND,
        "portfolio_learning_can_increase_leverage": PORTFOLIO_LEARNING_CAN_INCREASE_LEVERAGE,
        "portfolio_learning_can_increase_risk": PORTFOLIO_LEARNING_CAN_INCREASE_RISK,
        "portfolio_learning_can_mutate_live_config": PORTFOLIO_LEARNING_CAN_MUTATE_LIVE_CONFIG,
        "portfolio_learning_can_promote": PORTFOLIO_LEARNING_CAN_PROMOTE,
        "portfolio_learning_can_promote_to_live": PORTFOLIO_LEARNING_CAN_PROMOTE_TO_LIVE,
        "portfolio_learning_can_submit_order": PORTFOLIO_LEARNING_CAN_SUBMIT_ORDER,
        "portfolio_learning_can_use_confirm_token": PORTFOLIO_LEARNING_CAN_USE_CONFIRM_TOKEN,
        "portfolio_learning_can_write_live_config": PORTFOLIO_LEARNING_CAN_WRITE_LIVE_CONFIG,
        "portfolio_learning_domain": PORTFOLIO_LEARNING_DOMAIN,
        "portfolio_learning_has_runtime_authority": PORTFOLIO_LEARNING_HAS_RUNTIME_AUTHORITY,
        "portfolio_learning_present": PORTFOLIO_LEARNING_PRESENT,
        "portfolio_metrics": portfolio_metrics,
        "promotion_authority": PROMOTION_AUTHORITY,
        "robustness_suite_version": robustness_suite_version,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "self_learning_self_authorizing_separation": SELF_LEARNING_SELF_AUTHORIZING_SEPARATION,
        "strategy_and_portfolio_optimization_separated": (
            STRATEGY_AND_PORTFOLIO_OPTIMIZATION_SEPARATED
        ),
        "strong_single_strategy_is_not_automatic_portfolio_component": (
            STRONG_SINGLE_STRATEGY_IS_NOT_AUTOMATIC_PORTFOLIO_COMPONENT
        ),
    }
    evaluation_identity = derive_portfolio_learning_identity_v1(body)
    record = dict(body)
    record["evaluation_identity"] = evaluation_identity
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_portfolio_learning_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_portfolio_learning_v1 built identity=%s disposition=%s",
        evaluation_identity,
        overall_disposition,
    )
    return frozen


def derive_portfolio_learning_identity_v1(record_without_ids: Mapping[str, Any]) -> str:
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{PORTFOLIO_LEARNING_DOMAIN}.evaluation_identity",
        "payload": _plain_mapping(record_without_ids),
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def validate_canonical_portfolio_learning_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise PortfolioLearningValidationError("portfolio learning record must be a mapping")
    record = _plain_mapping(record)
    if record.get("schema_version") != SCHEMA_VERSION:
        raise PortfolioLearningValidationError("schema_version mismatch")
    if record.get("portfolio_learning_domain") != PORTFOLIO_LEARNING_DOMAIN:
        raise PortfolioLearningValidationError("portfolio_learning_domain mismatch")
    if record.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise PortfolioLearningValidationError("non-COMPLETE portfolio records are forbidden")
    if record.get("portfolio_learning_present") is not True:
        raise PortfolioLearningValidationError("portfolio_learning_present must be true")
    if record.get("strategy_and_portfolio_optimization_separated") is not True:
        raise PortfolioLearningValidationError(
            "strategy_and_portfolio_optimization_separated must be true"
        )
    if record.get("strong_single_strategy_is_not_automatic_portfolio_component") is not True:
        raise PortfolioLearningValidationError(
            "strong_single_strategy_is_not_automatic_portfolio_component must be true"
        )
    if record.get("applied_allocation") is not False:
        raise PortfolioLearningValidationError("applied_allocation must be false")
    if record.get("autonomous_allocation_apply") is not False:
        raise PortfolioLearningValidationError("autonomous_allocation_apply must be false")
    if record.get("autonomous_portfolio_promotion") is not False:
        raise PortfolioLearningValidationError("autonomous_portfolio_promotion must be false")
    if record.get("portfolio_learning_has_runtime_authority") is not False:
        raise PortfolioLearningValidationError(
            "portfolio_learning_has_runtime_authority must be false"
        )
    if record.get("portfolio_learning_can_mutate_live_config") is not False:
        raise PortfolioLearningValidationError(
            "portfolio_learning_can_mutate_live_config must be false"
        )
    if record.get("portfolio_learning_can_write_live_config") is not False:
        raise PortfolioLearningValidationError(
            "portfolio_learning_can_write_live_config must be false"
        )
    if record.get("portfolio_learning_can_promote") is not False:
        raise PortfolioLearningValidationError("portfolio_learning_can_promote must be false")
    if record.get("portfolio_learning_can_promote_to_live") is not False:
        raise PortfolioLearningValidationError(
            "portfolio_learning_can_promote_to_live must be false"
        )
    if record.get("portfolio_learning_can_increase_risk") is not False:
        raise PortfolioLearningValidationError("portfolio_learning_can_increase_risk must be false")
    if record.get("portfolio_learning_can_increase_leverage") is not False:
        raise PortfolioLearningValidationError(
            "portfolio_learning_can_increase_leverage must be false"
        )
    if record.get("portfolio_learning_can_fund") is not False:
        raise PortfolioLearningValidationError("portfolio_learning_can_fund must be false")
    if record.get("portfolio_learning_can_submit_order") is not False:
        raise PortfolioLearningValidationError("portfolio_learning_can_submit_order must be false")
    if record.get("portfolio_learning_can_arm") is not False:
        raise PortfolioLearningValidationError("portfolio_learning_can_arm must be false")
    if record.get("portfolio_learning_can_enable") is not False:
        raise PortfolioLearningValidationError("portfolio_learning_can_enable must be false")
    if record.get("portfolio_learning_can_create_confirm_token") is not False:
        raise PortfolioLearningValidationError(
            "portfolio_learning_can_create_confirm_token must be false"
        )
    if record.get("portfolio_learning_can_use_confirm_token") is not False:
        raise PortfolioLearningValidationError(
            "portfolio_learning_can_use_confirm_token must be false"
        )
    if record.get("portfolio_learning_can_authorize_canary") is not False:
        raise PortfolioLearningValidationError(
            "portfolio_learning_can_authorize_canary must be false"
        )
    if record.get("learning_may_autonomously_replace_core_logic") is not False:
        raise PortfolioLearningValidationError(
            "learning_may_autonomously_replace_core_logic must be false"
        )
    if record.get("self_learning_self_authorizing_separation") is not True:
        raise PortfolioLearningValidationError(
            "self_learning_self_authorizing_separation must be true"
        )
    if record.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise PortfolioLearningValidationError("promotion_authority must be NONE")
    if record.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise PortfolioLearningValidationError("runtime_authority_impact must be NONE")
    if record.get("comparison_ssot_version") != COMPARISON_SSOT_VERSION:
        raise PortfolioLearningValidationError("comparison_ssot_version mismatch")
    if record.get("metric_definitions") != METRIC_DEFINITION_VERSION:
        raise PortfolioLearningValidationError("metric_definitions must reuse the Phase 4 token")
    if record.get("robustness_suite_version") != ROBUSTNESS_SUITE_VERSION:
        raise PortfolioLearningValidationError(
            "robustness_suite_version must reuse the Phase 4 token"
        )
    members = record.get("member_results")
    if not isinstance(members, Sequence) or isinstance(members, (str, bytes)) or len(members) < 2:
        raise PortfolioLearningValidationError("at least two portfolio members are required")
    for item in members:
        if not isinstance(item, Mapping):
            raise PortfolioLearningValidationError("member_results entries must be mappings")
        if item.get("strategy_layer_status") != STATUS_OBSERVED:
            raise PortfolioLearningValidationError(
                "strategy_layer_status must remain STRATEGY_LAYER_OBSERVED"
            )
        if item.get("layer") != LAYER_PORTFOLIO:
            raise PortfolioLearningValidationError("member layer must be PORTFOLIO_LAYER")
    evaluation_identity = _require_sha256("evaluation_identity", record.get("evaluation_identity"))
    identity_payload = {
        key: value
        for key, value in record.items()
        if key not in {"evaluation_identity", "integrity"}
    }
    expected_identity = derive_portfolio_learning_identity_v1(identity_payload)
    if evaluation_identity != expected_identity:
        raise PortfolioLearningValidationError(
            "evaluation_identity does not match canonical content"
        )
    integrity = record.get("integrity")
    expected_integrity = compute_content_sha256(
        {key: value for key, value in record.items() if key != "integrity"}
    )
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise PortfolioLearningValidationError("integrity.content_sha256 mismatch")


def canonical_record_payload_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def _canonicalize_policy(policy: PortfolioPolicyV1) -> dict[str, Any]:
    version = _require_token("evaluation_policy_version", policy.evaluation_policy_version)
    if version != EVALUATION_POLICY_VERSION:
        raise PortfolioLearningValidationError("evaluation_policy_version mismatch")
    max_corr = _require_finite_number(
        "max_pairwise_abs_correlation", policy.max_pairwise_abs_correlation
    )
    if max_corr < 0.0 or max_corr > 1.0:
        raise PortfolioLearningValidationError("max_pairwise_abs_correlation must be in [0, 1]")
    max_concentration = _require_finite_number("max_concentration", policy.max_concentration)
    if max_concentration <= 0.0 or max_concentration > 1.0:
        raise PortfolioLearningValidationError("max_concentration must be in (0, 1]")
    min_diversification = _require_finite_number("min_diversification", policy.min_diversification)
    max_abs_drawdown = _require_finite_number(
        "max_abs_portfolio_drawdown", policy.max_abs_portfolio_drawdown
    )
    if max_abs_drawdown < 0.0:
        raise PortfolioLearningValidationError("max_abs_portfolio_drawdown must be >= 0")
    max_turnover = _require_finite_number("max_turnover", policy.max_turnover)
    if max_turnover < 0.0:
        raise PortfolioLearningValidationError("max_turnover must be >= 0")
    min_capacity = _require_finite_number("min_capacity", policy.min_capacity)
    min_allocation_stability = _require_finite_number(
        "min_allocation_stability", policy.min_allocation_stability
    )
    max_risk_contribution = _require_finite_number(
        "max_risk_contribution", policy.max_risk_contribution
    )
    if max_risk_contribution <= 0.0 or max_risk_contribution > 1.0:
        raise PortfolioLearningValidationError("max_risk_contribution must be in (0, 1]")
    return {
        "evaluation_policy_version": version,
        "max_abs_portfolio_drawdown": max_abs_drawdown,
        "max_concentration": max_concentration,
        "max_pairwise_abs_correlation": max_corr,
        "max_risk_contribution": max_risk_contribution,
        "max_turnover": max_turnover,
        "min_allocation_stability": min_allocation_stability,
        "min_capacity": min_capacity,
        "min_diversification": min_diversification,
    }


def _canonicalize_members(members: Sequence[PortfolioMemberV1]) -> list[dict[str, Any]]:
    if not isinstance(members, Sequence) or isinstance(members, (str, bytes)):
        raise PortfolioLearningValidationError("members must be a sequence")
    if len(members) < 2:
        raise PortfolioLearningValidationError("at least two portfolio members are required")
    canonical: list[dict[str, Any]] = []
    seen: set[str] = set()
    weight_sum = 0.0
    for index, member in enumerate(members):
        experiment_id = _experiment_id(member.candidate)
        if experiment_id in seen:
            raise PortfolioLearningValidationError(
                f"duplicate member experiment_id: {experiment_id}"
            )
        seen.add(experiment_id)
        weight = _require_finite_number(f"members[{index}].weight", member.weight)
        if weight <= 0.0:
            raise PortfolioLearningValidationError("member weight must be positive")
        weight_sum += weight
        strategy_layer = {
            field_name: _require_finite_number(
                f"members[{index}].strategy_layer.{field_name}",
                getattr(member.strategy_layer, field_name),
            )
            for field_name in STRATEGY_LAYER_FIELDS
        }
        canonical.append(
            {
                "candidate": member.candidate,
                "experiment_id": experiment_id,
                "fee_drag": _require_finite_number(f"members[{index}].fee_drag", member.fee_drag),
                "marginal_risk": _require_finite_number(
                    f"members[{index}].marginal_risk", member.marginal_risk
                ),
                "risk_contribution": _require_finite_number(
                    f"members[{index}].risk_contribution", member.risk_contribution
                ),
                "slippage": _require_finite_number(f"members[{index}].slippage", member.slippage),
                "strategy_layer": strategy_layer,
                "weight": weight,
            }
        )
    if abs(weight_sum - 1.0) > WEIGHT_SUM_ABS_TOLERANCE:
        raise PortfolioLearningValidationError("member weights must sum to 1")
    canonical.sort(key=lambda item: item["experiment_id"])
    return canonical


def _canonicalize_pairwise(
    pairwise: Sequence[PairwiseObservationV1],
    experiment_ids: Sequence[str],
    compatibility_contract: ComparisonCompatibilityContractV1 | None,
    created_at: str,
    bound_members: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(pairwise, Sequence) or isinstance(pairwise, (str, bytes)):
        raise PortfolioLearningValidationError("pairwise observations must be a sequence")
    members_by_id = {item["experiment_id"]: item for item in bound_members}
    expected_pairs = {
        tuple(sorted((left, right)))
        for index, left in enumerate(experiment_ids)
        for right in experiment_ids[index + 1 :]
    }
    seen: set[tuple[str, str]] = set()
    canonical: list[dict[str, Any]] = []
    for index, item in enumerate(pairwise):
        left_id = _require_sha256(f"pairwise[{index}].left_experiment_id", item.left_experiment_id)
        right_id = _require_sha256(
            f"pairwise[{index}].right_experiment_id", item.right_experiment_id
        )
        if left_id == right_id:
            raise PortfolioLearningValidationError("pairwise self-pairs are forbidden")
        pair_key = tuple(sorted((left_id, right_id)))
        if pair_key in seen:
            raise PortfolioLearningValidationError("duplicate pairwise observation")
        if pair_key not in expected_pairs:
            raise PortfolioLearningValidationError("pairwise observation is not a member pair")
        seen.add(pair_key)
        correlation = _require_finite_number(f"pairwise[{index}].correlation", item.correlation)
        if correlation < -1.0 or correlation > 1.0:
            raise PortfolioLearningValidationError("correlation must be in [-1, 1]")
        covariance = _require_finite_number(f"pairwise[{index}].covariance", item.covariance)
        left_member = members_by_id[pair_key[0]]
        right_member = members_by_id[pair_key[1]]
        comparison = canonical_record_payload(
            build_canonical_comparison_result_v1(
                CanonicalComparisonRequestV1(
                    left=left_member["candidate"],
                    right=right_member["candidate"],
                    created_at=created_at,
                    compatibility_contract=compatibility_contract,
                )
            )
        )
        canonical.append(
            {
                "comparison_identity": comparison["comparison_identity"],
                "correlation": correlation,
                "covariance": covariance,
                "left_experiment_id": pair_key[0],
                "overall_comparability": comparison["overall_comparability"],
                "rejection_reasons": list(comparison["rejection_reasons"]),
                "right_experiment_id": pair_key[1],
            }
        )
    missing = expected_pairs - seen
    if missing:
        raise PortfolioLearningValidationError(
            "pairwise correlation/covariance observations are missing"
        )
    canonical.sort(key=lambda item: (item["left_experiment_id"], item["right_experiment_id"]))
    return canonical


def _canonicalize_portfolio_metrics(
    *,
    diversification: float,
    concentration: float,
    portfolio_drawdown: float,
    turnover: float,
    capacity: float,
    allocation_stability: float,
    max_weight: float,
) -> dict[str, float]:
    metrics = {
        "allocation_stability": _require_finite_number(
            "allocation_stability", allocation_stability
        ),
        "capacity": _require_finite_number("capacity", capacity),
        "concentration": _require_finite_number("concentration", concentration),
        "diversification": _require_finite_number("diversification", diversification),
        "portfolio_drawdown": _require_finite_number("portfolio_drawdown", portfolio_drawdown),
        "turnover": _require_finite_number("turnover", turnover),
    }
    if metrics["concentration"] + WEIGHT_SUM_ABS_TOLERANCE < max_weight:
        raise PortfolioLearningValidationError(
            "concentration cannot be below the maximum explicit member weight"
        )
    return metrics


def _evaluate_portfolio_gates(
    *,
    bound_members: Sequence[Mapping[str, Any]],
    pairwise_results: Sequence[Mapping[str, Any]],
    portfolio_metrics: Mapping[str, float],
    policy: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    for pair in pairwise_results:
        if abs(float(pair["correlation"])) > float(policy["max_pairwise_abs_correlation"]):
            failures.append("max_pairwise_abs_correlation")
            break
    max_weight = max(float(item["weight"]) for item in bound_members)
    if max_weight > float(policy["max_concentration"]):
        failures.append("max_concentration")
    if float(portfolio_metrics["concentration"]) > float(policy["max_concentration"]):
        if "max_concentration" not in failures:
            failures.append("max_concentration")
    if float(portfolio_metrics["diversification"]) < float(policy["min_diversification"]):
        failures.append("min_diversification")
    if abs(float(portfolio_metrics["portfolio_drawdown"])) > float(
        policy["max_abs_portfolio_drawdown"]
    ):
        failures.append("max_abs_portfolio_drawdown")
    if float(portfolio_metrics["turnover"]) > float(policy["max_turnover"]):
        failures.append("max_turnover")
    if float(portfolio_metrics["capacity"]) < float(policy["min_capacity"]):
        failures.append("min_capacity")
    if float(portfolio_metrics["allocation_stability"]) < float(policy["min_allocation_stability"]):
        failures.append("min_allocation_stability")
    for item in bound_members:
        if float(item["risk_contribution"]) > float(policy["max_risk_contribution"]):
            failures.append("max_risk_contribution")
            break
    return failures


def _experiment_id(candidate: ComparisonCandidateV1) -> str:
    identity = candidate.experiment_identity
    if not isinstance(identity, Mapping):
        raise PortfolioLearningValidationError("experiment_identity present and valid is required")
    payload = _plain_mapping(identity)
    try:
        validate_canonical_experiment_identity_v1(payload)
    except CanonicalExperimentIdentityError as exc:
        raise PortfolioLearningValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    experiment_id = derive_experiment_id_v1(str(payload["identity_digest"]))
    if candidate.experiment_id is not None:
        provided = _require_sha256("experiment_id", candidate.experiment_id)
        if provided != experiment_id:
            raise PortfolioLearningValidationError(
                "experiment_id is not bound to the Canonical Experiment Identity digest"
            )
    return experiment_id


def _canonicalize_evidence_refs(value: Any, experiment_ids: Sequence[str]) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise PortfolioLearningValidationError("evidence_refs must be a sequence")
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    bound_ids: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise PortfolioLearningValidationError(f"evidence_refs[{index}] must be a mapping")
        kind = item.get("kind")
        if kind not in _EVIDENCE_KINDS:
            raise PortfolioLearningValidationError(f"evidence_refs[{index}].kind is unsupported")
        digest = _require_sha256(f"evidence_refs[{index}].digest", item.get("digest"))
        if kind == EVIDENCE_KIND_EXPERIMENT_RECORD:
            ref = _require_sha256(f"evidence_refs[{index}].ref", item.get("ref"))
            if ref in experiment_ids:
                bound_ids.add(ref)
        else:
            ref = _require_relative_artifact_ref(f"evidence_refs[{index}].ref", item.get("ref"))
        extra_keys = set(str(key) for key in item.keys()) - {"kind", "ref", "digest"}
        if extra_keys:
            raise PortfolioLearningValidationError(
                f"evidence_refs[{index}] contains unsupported keys: {sorted(extra_keys)}"
            )
        key = (str(kind), ref)
        if key in seen:
            raise PortfolioLearningValidationError("duplicate evidence_refs are forbidden")
        seen.add(key)
        refs.append({"digest": digest, "kind": str(kind), "ref": ref})
    missing = [experiment_id for experiment_id in experiment_ids if experiment_id not in bound_ids]
    if missing:
        raise PortfolioLearningValidationError(
            "evidence_refs must include the bound EXPERIMENT_RECORD for every member"
        )
    refs.sort(key=lambda item: (item["kind"], item["ref"]))
    return refs


def _require_relative_artifact_ref(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or value.startswith("/"):
        raise PortfolioLearningValidationError(f"{field_name} must be a relative POSIX path")
    if ".." in value.split("/"):
        raise PortfolioLearningValidationError(
            f"{field_name} path traversal or empty segments are forbidden"
        )
    if "\\" in value:
        raise PortfolioLearningValidationError(
            f"{field_name} must use store-/repo-relative POSIX paths"
        )
    return value


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise PortfolioLearningValidationError(
            f"{field_name} must be a lowercase sha256 hex digest"
        )
    return value


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise PortfolioLearningValidationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


def _require_token(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not _TOKEN_RE.fullmatch(value):
        raise PortfolioLearningValidationError(f"{field_name} is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise PortfolioLearningValidationError(
            f"{field_name} cannot use implicit unavailable tokens"
        )
    return value


def _require_finite_number(field_name: str, value: Any) -> float:
    if value is None:
        raise PortfolioLearningValidationError(
            f"{field_name} is missing; silent zero defaults are forbidden"
        )
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PortfolioLearningValidationError(f"{field_name} must be an explicit finite number")
    number = float(value)
    if not math.isfinite(number):
        raise PortfolioLearningValidationError(
            f"non-finite numeric values are forbidden in {field_name}"
        )
    return number


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_freeze(item) for item in value]
    return value


def _plain_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_mapping(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_mapping(item) for item in value]
    return value


__all__ = [
    "AUTONOMOUS_ALLOCATION_APPLY",
    "CanonicalPortfolioLearningRequestV1",
    "DISPOSITION_ELIGIBLE",
    "DISPOSITION_INELIGIBLE",
    "DISPOSITION_REJECTED_COMPARABILITY",
    "PORTFOLIO_LEARNING_CAN_MUTATE_LIVE_CONFIG",
    "PORTFOLIO_LEARNING_CAN_PROMOTE",
    "PORTFOLIO_LEARNING_HAS_RUNTIME_AUTHORITY",
    "PORTFOLIO_LEARNING_PRESENT",
    "PROMOTION_AUTHORITY",
    "PairwiseObservationV1",
    "PortfolioLearningValidationError",
    "PortfolioMemberV1",
    "PortfolioPolicyV1",
    "STATUS_ELIGIBLE",
    "STATUS_INELIGIBLE",
    "STATUS_OBSERVED",
    "STRATEGY_AND_PORTFOLIO_OPTIMIZATION_SEPARATED",
    "StrategyLayerObservationV1",
    "build_canonical_portfolio_learning_v1",
    "canonical_record_payload_v1",
    "validate_canonical_portfolio_learning_v1",
]
