"""Phase 5 Canonical Comparison SSOT v1 (research evidence only).

Deterministic comparability for Canonical Experiment Identity bound
candidates. Experiments may be ranked only when every required comparison
dimension is identical or covered by an explicit versioned compatibility
contract. This layer reuses Phase 1 identity and Phase 2 experiment_id.
It has no runtime, order, live, funding, canary, promotion, champion-
challenger, or config-write authority.

Missing fee, funding, split, robustness version, or market universe is
never treated as compatible.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityError,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_comparison_ssot_v1"
COMPARISON_DOMAIN: Final[str] = "peak_trade.canonical_comparison_ssot.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
COMPARISON_CONTRACT_VERSION: Final[str] = SCHEMA_VERSION
COMPATIBILITY_CONTRACT_NONE: Final[str] = "NONE"

COMPARISON_SSOT_HAS_RUNTIME_AUTHORITY: Final[bool] = False
COMPARISON_SSOT_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
COMPARISON_SSOT_CAN_PROMOTE: Final[bool] = False
COMPARISON_SSOT_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
COMPARISON_SSOT_CAN_INCREASE_RISK: Final[bool] = False
COMPARISON_SSOT_CAN_INCREASE_LEVERAGE: Final[bool] = False
COMPARISON_SSOT_CAN_FUND: Final[bool] = False
COMPARISON_SSOT_CAN_SUBMIT_ORDER: Final[bool] = False
COMPARISON_SSOT_CAN_ARM: Final[bool] = False
COMPARISON_SSOT_CAN_ENABLE: Final[bool] = False
COMPARISON_SSOT_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
COMPARISON_SSOT_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
COMPARISON_SSOT_CAN_AUTHORIZE_CANARY: Final[bool] = False
COMPARISON_SSOT_CAN_PROMOTE_TO_LIVE: Final[bool] = False
COMPARISON_SSOT_CAN_RANK_NON_COMPARABLE: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
CHAMPION_CHALLENGER_IMPLEMENTED: Final[bool] = False
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

OVERALL_COMPARABLE: Final[str] = "COMPARABLE"
OVERALL_REJECTED: Final[str] = "COMPARISON_REJECTED"
DIMENSION_IDENTICAL: Final[str] = "IDENTICAL"
DIMENSION_COMPATIBLE: Final[str] = "COMPATIBLE"
DIMENSION_MISMATCH: Final[str] = "MISMATCH"
DIMENSION_MISSING: Final[str] = "MISSING"
RANKING_STATUS_RANKED: Final[str] = "RANKED"
RANKING_STATUS_REJECTED: Final[str] = "RANKING_REJECTED"
RANKING_REASON_NON_COMPARABLE: Final[str] = "NON_COMPARABLE_CANDIDATE"

COMPARISON_DIMENSIONS: Final[tuple[str, ...]] = (
    "dataset_identity",
    "split_policy",
    "fee_model",
    "slippage_model",
    "funding_model",
    "risk_policy",
    "portfolio_constraints",
    "robustness_suite_version",
    "metric_definitions",
    "time_horizon",
    "market_universe",
)
IDENTITY_DIMENSION_FIELDS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "dataset_identity": "dataset_digest",
        "split_policy": "split_policy_digest",
        "fee_model": "fee_model_digest",
        "slippage_model": "slippage_model_digest",
        "funding_model": "funding_model_digest",
        "risk_policy": "risk_policy_digest",
        "portfolio_constraints": "portfolio_digest",
    }
)
EXPLICIT_DIMENSIONS: Final[tuple[str, ...]] = (
    "robustness_suite_version",
    "metric_definitions",
    "time_horizon",
    "market_universe",
)

_CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_INSTRUMENT_RE = re.compile(r"^[A-Za-z0-9._:/-]{1,64}$")
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
    }
)

_LOGGER = logging.getLogger(__name__)


class ComparisonValidationError(ValueError):
    """Fail-closed Canonical Comparison SSOT v1 validation error."""


class ComparisonRankingRejectedError(ComparisonValidationError):
    """Non-comparable candidates cannot be ranked."""


@dataclass(frozen=True)
class ComparisonCandidateV1:
    experiment_identity: Mapping[str, Any]
    robustness_suite_version: Any = None
    metric_definitions: Any = None
    time_horizon: Any = None
    market_universe: Any = None
    experiment_id: str | None = None
    evidence_refs: Sequence[Mapping[str, Any]] = ()


@dataclass(frozen=True)
class CompatibilityRuleV1:
    dimension: str
    left_value: str
    right_value: str


@dataclass(frozen=True)
class ComparisonCompatibilityContractV1:
    contract_version: str
    rules: Sequence[CompatibilityRuleV1] = ()


@dataclass(frozen=True)
class CanonicalComparisonRequestV1:
    left: ComparisonCandidateV1
    right: ComparisonCandidateV1
    created_at: str
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None


@dataclass(frozen=True)
class CanonicalComparisonRankingRequestV1:
    candidates: Sequence[ComparisonCandidateV1]
    scores: Mapping[str, float]
    created_at: str
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None
    score_metric: str = "explicit_score"


def build_canonical_comparison_result_v1(
    request: CanonicalComparisonRequestV1,
) -> Mapping[str, Any]:
    left = _bound_candidate(request.left)
    right = _bound_candidate(request.right)
    created_at = _require_created_at(request.created_at)
    contract, contract_version, rule_index = _canonicalize_contract(request.compatibility_contract)
    dimension_results, rejection_reasons = _compare_dimensions(left, right, rule_index)
    overall = OVERALL_COMPARABLE if not rejection_reasons else OVERALL_REJECTED
    evidence_refs = _merge_evidence_refs(left, right)
    comparison_identity = derive_comparison_identity_v1(
        left_experiment_id=left["experiment_id"],
        right_experiment_id=right["experiment_id"],
        compatibility_contract_version=contract_version,
        dimension_results=dimension_results,
        overall_comparability=overall,
    )
    record = {
        "champion_challenger_implemented": CHAMPION_CHALLENGER_IMPLEMENTED,
        "comparability_dimensions": list(COMPARISON_DIMENSIONS),
        "comparison_contract_version": COMPARISON_CONTRACT_VERSION,
        "comparison_domain": COMPARISON_DOMAIN,
        "comparison_identity": comparison_identity,
        "comparison_ssot_can_arm": COMPARISON_SSOT_CAN_ARM,
        "comparison_ssot_can_authorize_canary": COMPARISON_SSOT_CAN_AUTHORIZE_CANARY,
        "comparison_ssot_can_create_confirm_token": COMPARISON_SSOT_CAN_CREATE_CONFIRM_TOKEN,
        "comparison_ssot_can_enable": COMPARISON_SSOT_CAN_ENABLE,
        "comparison_ssot_can_fund": COMPARISON_SSOT_CAN_FUND,
        "comparison_ssot_can_increase_leverage": COMPARISON_SSOT_CAN_INCREASE_LEVERAGE,
        "comparison_ssot_can_increase_risk": COMPARISON_SSOT_CAN_INCREASE_RISK,
        "comparison_ssot_can_mutate_live_config": COMPARISON_SSOT_CAN_MUTATE_LIVE_CONFIG,
        "comparison_ssot_can_promote": COMPARISON_SSOT_CAN_PROMOTE,
        "comparison_ssot_can_promote_to_live": COMPARISON_SSOT_CAN_PROMOTE_TO_LIVE,
        "comparison_ssot_can_rank_non_comparable": COMPARISON_SSOT_CAN_RANK_NON_COMPARABLE,
        "comparison_ssot_can_submit_order": COMPARISON_SSOT_CAN_SUBMIT_ORDER,
        "comparison_ssot_can_use_confirm_token": COMPARISON_SSOT_CAN_USE_CONFIRM_TOKEN,
        "comparison_ssot_can_write_live_config": COMPARISON_SSOT_CAN_WRITE_LIVE_CONFIG,
        "comparison_ssot_has_runtime_authority": COMPARISON_SSOT_HAS_RUNTIME_AUTHORITY,
        "compatibility_contract": contract,
        "compatibility_contract_version": contract_version,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "dimension_results": dimension_results,
        "evidence_refs": evidence_refs,
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "left_experiment_id": left["experiment_id"],
        "left_identity_digest": left["identity_digest"],
        "overall_comparability": overall,
        "promotion_authority": PROMOTION_AUTHORITY,
        "rejection_reasons": rejection_reasons,
        "right_experiment_id": right["experiment_id"],
        "right_identity_digest": right["identity_digest"],
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "self_learning_self_authorizing_separation": SELF_LEARNING_SELF_AUTHORIZING_SEPARATION,
    }
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_comparison_result_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_comparison_ssot_v1 built identity=%s overall=%s reasons=%s",
        comparison_identity,
        overall,
        rejection_reasons,
    )
    return frozen


def rank_comparable_candidates_v1(
    request: CanonicalComparisonRankingRequestV1,
) -> Mapping[str, Any]:
    if len(request.candidates) < 2:
        raise ComparisonValidationError("ranking requires at least two candidates")
    created_at = _require_created_at(request.created_at)
    bound = [_bound_candidate(item) for item in request.candidates]
    experiment_ids = [item["experiment_id"] for item in bound]
    if len(set(experiment_ids)) != len(experiment_ids):
        raise ComparisonValidationError("ranking candidates must have unique experiment_id values")
    scores = _canonicalize_scores(request.scores, experiment_ids)
    pair_results: list[dict[str, Any]] = []
    rejection_reasons: list[str] = []
    for index, left_candidate in enumerate(request.candidates[:-1]):
        for right_candidate in request.candidates[index + 1 :]:
            pair = build_canonical_comparison_result_v1(
                CanonicalComparisonRequestV1(
                    left=left_candidate,
                    right=right_candidate,
                    created_at=created_at,
                    compatibility_contract=request.compatibility_contract,
                )
            )
            pair_payload = canonical_record_payload(pair)
            pair_results.append(
                {
                    "comparison_identity": pair_payload["comparison_identity"],
                    "left_experiment_id": pair_payload["left_experiment_id"],
                    "overall_comparability": pair_payload["overall_comparability"],
                    "rejection_reasons": list(pair_payload["rejection_reasons"]),
                    "right_experiment_id": pair_payload["right_experiment_id"],
                }
            )
            if pair_payload["overall_comparability"] != OVERALL_COMPARABLE:
                rejection_reasons.extend(
                    f"{pair_payload['left_experiment_id']}:{pair_payload['right_experiment_id']}:"
                    f"{reason}"
                    for reason in pair_payload["rejection_reasons"]
                )
    ranking_status = RANKING_STATUS_RANKED if not rejection_reasons else RANKING_STATUS_REJECTED
    ranked_ids: list[str] = []
    if ranking_status == RANKING_STATUS_RANKED:
        ranked_ids = sorted(
            experiment_ids,
            key=lambda experiment_id: (-scores[experiment_id], experiment_id),
        )
    ranking_identity = compute_content_sha256(
        {
            "digest_algorithm": DIGEST_ALGORITHM,
            "digest_domain": f"{COMPARISON_DOMAIN}.ranking",
            "payload": {
                "created_at": created_at,
                "experiment_ids": experiment_ids,
                "pair_results": pair_results,
                "ranked_experiment_ids": ranked_ids,
                "ranking_status": ranking_status,
                "rejection_reasons": rejection_reasons,
                "score_metric": _require_token("score_metric", request.score_metric),
                "scores": scores,
            },
            "schema_version": SCHEMA_VERSION,
        }
    )
    record = {
        "champion_challenger_implemented": CHAMPION_CHALLENGER_IMPLEMENTED,
        "comparison_contract_version": COMPARISON_CONTRACT_VERSION,
        "comparison_domain": COMPARISON_DOMAIN,
        "comparison_ssot_can_promote": COMPARISON_SSOT_CAN_PROMOTE,
        "comparison_ssot_can_rank_non_comparable": COMPARISON_SSOT_CAN_RANK_NON_COMPARABLE,
        "comparison_ssot_has_runtime_authority": COMPARISON_SSOT_HAS_RUNTIME_AUTHORITY,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "pair_results": pair_results,
        "promotion_authority": PROMOTION_AUTHORITY,
        "ranked_experiment_ids": ranked_ids,
        "ranking_identity": ranking_identity,
        "ranking_reason": (
            None if ranking_status == RANKING_STATUS_RANKED else RANKING_REASON_NON_COMPARABLE
        ),
        "ranking_status": ranking_status,
        "rejection_reasons": rejection_reasons,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "score_metric": _require_token("score_metric", request.score_metric),
        "scores": scores,
        "self_learning_self_authorizing_separation": SELF_LEARNING_SELF_AUTHORIZING_SEPARATION,
    }
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    frozen = _freeze(record)
    if ranking_status == RANKING_STATUS_REJECTED:
        _LOGGER.info(
            "canonical_comparison_ssot_v1 ranking rejected reasons=%s",
            rejection_reasons,
        )
    return frozen


def derive_comparison_identity_v1(
    *,
    left_experiment_id: str,
    right_experiment_id: str,
    compatibility_contract_version: str,
    dimension_results: Sequence[Mapping[str, Any]],
    overall_comparability: str,
) -> str:
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{COMPARISON_DOMAIN}.comparison_identity",
        "payload": {
            "compatibility_contract_version": compatibility_contract_version,
            "comparison_contract_version": COMPARISON_CONTRACT_VERSION,
            "dimension_results": list(dimension_results),
            "left_experiment_id": left_experiment_id,
            "overall_comparability": overall_comparability,
            "right_experiment_id": right_experiment_id,
        },
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def validate_canonical_comparison_result_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise ComparisonValidationError("comparison result must be a mapping")
    payload = _plain_mapping(record)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ComparisonValidationError("schema_version mismatch")
    if payload.get("comparison_domain") != COMPARISON_DOMAIN:
        raise ComparisonValidationError("comparison_domain mismatch")
    if payload.get("comparison_contract_version") != COMPARISON_CONTRACT_VERSION:
        raise ComparisonValidationError("comparison_contract_version mismatch")
    if payload.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise ComparisonValidationError("non-COMPLETE comparison results are forbidden")
    if payload.get("comparison_ssot_has_runtime_authority") is not False:
        raise ComparisonValidationError("comparison_ssot_has_runtime_authority must be false")
    if payload.get("comparison_ssot_can_mutate_live_config") is not False:
        raise ComparisonValidationError("comparison_ssot_can_mutate_live_config must be false")
    if payload.get("comparison_ssot_can_promote") is not False:
        raise ComparisonValidationError("comparison_ssot_can_promote must be false")
    if payload.get("comparison_ssot_can_rank_non_comparable") is not False:
        raise ComparisonValidationError("comparison_ssot_can_rank_non_comparable must be false")
    if payload.get("champion_challenger_implemented") is not False:
        raise ComparisonValidationError("champion_challenger_implemented must be false")
    if payload.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise ComparisonValidationError("promotion_authority must be NONE")
    if payload.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise ComparisonValidationError("runtime_authority_impact must be NONE")
    overall = payload.get("overall_comparability")
    if overall not in {OVERALL_COMPARABLE, OVERALL_REJECTED}:
        raise ComparisonValidationError("overall_comparability is not a canonical value")
    dimensions = payload.get("comparability_dimensions")
    if dimensions != list(COMPARISON_DIMENSIONS):
        raise ComparisonValidationError("comparability_dimensions mismatch")
    dimension_results = payload.get("dimension_results")
    if not isinstance(dimension_results, list) or len(dimension_results) != len(
        COMPARISON_DIMENSIONS
    ):
        raise ComparisonValidationError("dimension_results must cover every comparison dimension")
    observed_ids = [item.get("dimension") for item in dimension_results]
    if observed_ids != list(COMPARISON_DIMENSIONS):
        raise ComparisonValidationError("dimension_results order must be canonical")
    rejection_reasons = payload.get("rejection_reasons")
    if not isinstance(rejection_reasons, list) or any(
        not isinstance(item, str) or not item.strip() for item in rejection_reasons
    ):
        raise ComparisonValidationError("rejection_reasons must be a list of non-empty strings")
    if overall == OVERALL_COMPARABLE and rejection_reasons:
        raise ComparisonValidationError("COMPARABLE results cannot carry rejection_reasons")
    if overall == OVERALL_REJECTED and not rejection_reasons:
        raise ComparisonValidationError("COMPARISON_REJECTED requires rejection_reasons")
    _require_sha256("left_experiment_id", payload.get("left_experiment_id"))
    _require_sha256("right_experiment_id", payload.get("right_experiment_id"))
    _require_sha256("left_identity_digest", payload.get("left_identity_digest"))
    _require_sha256("right_identity_digest", payload.get("right_identity_digest"))
    _require_created_at(payload.get("created_at"))
    expected_identity = derive_comparison_identity_v1(
        left_experiment_id=str(payload["left_experiment_id"]),
        right_experiment_id=str(payload["right_experiment_id"]),
        compatibility_contract_version=str(payload["compatibility_contract_version"]),
        dimension_results=dimension_results,
        overall_comparability=str(overall),
    )
    if payload.get("comparison_identity") != expected_identity:
        raise ComparisonValidationError("comparison_identity mismatch")
    expected_integrity = compute_content_sha256(
        {key: value for key, value in payload.items() if key != "integrity"}
    )
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise ComparisonValidationError("integrity.content_sha256 mismatch")


def canonical_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def _bound_candidate(candidate: ComparisonCandidateV1) -> dict[str, Any]:
    identity = _require_identity(candidate.experiment_identity)
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if candidate.experiment_id is not None:
        provided = _require_sha256("experiment_id", candidate.experiment_id)
        if provided != experiment_id:
            raise ComparisonValidationError(
                "experiment_id is not bound to the Canonical Experiment Identity digest"
            )
    dimensions = _extract_dimensions(candidate, identity)
    evidence_refs = _canonicalize_evidence_refs(
        candidate.evidence_refs,
        experiment_id=experiment_id,
        identity_digest=str(identity["identity_digest"]),
    )
    return {
        "dimensions": dimensions,
        "evidence_refs": evidence_refs,
        "experiment_id": experiment_id,
        "identity_digest": identity["identity_digest"],
    }


def _extract_dimensions(
    candidate: ComparisonCandidateV1,
    identity: Mapping[str, Any],
) -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for dimension, field_name in IDENTITY_DIMENSION_FIELDS.items():
        values[dimension] = _optional_digest(field_name, identity.get(field_name))
    values["robustness_suite_version"] = _optional_token(
        "robustness_suite_version", candidate.robustness_suite_version
    )
    values["metric_definitions"] = _optional_token(
        "metric_definitions", candidate.metric_definitions
    )
    values["time_horizon"] = _optional_time_horizon(candidate.time_horizon)
    values["market_universe"] = _optional_market_universe(candidate.market_universe)
    return values


def _compare_dimensions(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    rule_index: set[tuple[str, str, str]],
) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    rejection_reasons: list[str] = []
    left_values = left["dimensions"]
    right_values = right["dimensions"]
    for dimension in COMPARISON_DIMENSIONS:
        left_value = left_values.get(dimension)
        right_value = right_values.get(dimension)
        if left_value is None or right_value is None:
            status = DIMENSION_MISSING
            reason = f"{dimension}:MISSING"
        elif left_value == right_value:
            status = DIMENSION_IDENTICAL
            reason = None
        elif (dimension, *sorted((left_value, right_value))) in rule_index:
            status = DIMENSION_COMPATIBLE
            reason = None
        else:
            status = DIMENSION_MISMATCH
            reason = f"{dimension}:MISMATCH"
        results.append(
            {
                "dimension": dimension,
                "left_value": left_value,
                "reason": reason,
                "right_value": right_value,
                "status": status,
            }
        )
        if reason is not None:
            rejection_reasons.append(reason)
    return results, rejection_reasons


def _canonicalize_contract(
    contract: ComparisonCompatibilityContractV1 | None,
) -> tuple[dict[str, Any] | None, str, set[tuple[str, str, str]]]:
    if contract is None:
        return None, COMPATIBILITY_CONTRACT_NONE, set()
    version = _require_token("compatibility_contract.contract_version", contract.contract_version)
    if version == COMPATIBILITY_CONTRACT_NONE:
        raise ComparisonValidationError(
            "compatibility_contract.contract_version cannot be NONE when a contract is supplied"
        )
    rules: list[dict[str, str]] = []
    index: set[tuple[str, str, str]] = set()
    for rule in contract.rules:
        dimension = _require_dimension(rule.dimension)
        left_value = _require_comparison_value("compatibility_rule.left_value", rule.left_value)
        right_value = _require_comparison_value("compatibility_rule.right_value", rule.right_value)
        if left_value == right_value:
            raise ComparisonValidationError(
                "compatibility rules cannot map a value to itself; identity is implicit"
            )
        canonical = {
            "dimension": dimension,
            "left_value": left_value,
            "right_value": right_value,
        }
        ordered = (dimension, *sorted((left_value, right_value)))
        if ordered in index:
            raise ComparisonValidationError("duplicate compatibility rule")
        index.add(ordered)
        rules.append(canonical)
    rules.sort(key=lambda item: (item["dimension"], item["left_value"], item["right_value"]))
    return (
        {
            "contract_version": version,
            "rules": rules,
        },
        version,
        index,
    )


def _merge_evidence_refs(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> list[dict[str, str]]:
    merged = list(left["evidence_refs"]) + list(right["evidence_refs"])
    unique: dict[tuple[str, str, str], dict[str, str]] = {}
    for item in merged:
        unique[(item["kind"], item["ref"], item["digest"])] = item
    return [unique[key] for key in sorted(unique)]


def _canonicalize_evidence_refs(
    refs: Sequence[Mapping[str, Any]],
    *,
    experiment_id: str,
    identity_digest: str,
) -> list[dict[str, str]]:
    items = [
        {
            "digest": identity_digest,
            "kind": "EXPERIMENT_RECORD",
            "ref": experiment_id,
        }
    ]
    if refs:
        for index, raw in enumerate(refs):
            if not isinstance(raw, Mapping):
                raise ComparisonValidationError(f"evidence_refs[{index}] must be a mapping")
            kind = _require_token(f"evidence_refs[{index}].kind", raw.get("kind"))
            ref = _require_token(f"evidence_refs[{index}].ref", raw.get("ref"))
            digest = _require_sha256(f"evidence_refs[{index}].digest", raw.get("digest"))
            items.append({"digest": digest, "kind": kind, "ref": ref})
    unique: dict[tuple[str, str, str], dict[str, str]] = {}
    for item in items:
        unique[(item["kind"], item["ref"], item["digest"])] = item
    return [unique[key] for key in sorted(unique)]


def _canonicalize_scores(
    scores: Mapping[str, float],
    experiment_ids: Sequence[str],
) -> dict[str, float]:
    if not isinstance(scores, Mapping):
        raise ComparisonValidationError("scores must be a mapping")
    canonical: dict[str, float] = {}
    for experiment_id in experiment_ids:
        if experiment_id not in scores:
            raise ComparisonValidationError(f"scores missing experiment_id {experiment_id}")
        value = scores[experiment_id]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ComparisonValidationError(f"scores[{experiment_id}] must be a finite number")
        number = float(value)
        if not math.isfinite(number):
            raise ComparisonValidationError(f"scores[{experiment_id}] must be finite")
        canonical[experiment_id] = number
    extra = set(str(key) for key in scores.keys()) - set(experiment_ids)
    if extra:
        raise ComparisonValidationError(
            f"scores contain unknown experiment_id values: {sorted(extra)}"
        )
    return canonical


def _optional_digest(field_name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    lowered = value.strip().lower()
    if lowered in _UNAVAILABLE_TOKENS:
        return None
    if not is_valid_sha256_hex(value):
        raise ComparisonValidationError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _optional_token(field_name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        return None
    if not _TOKEN_RE.fullmatch(value):
        raise ComparisonValidationError(f"{field_name} is missing or malformed")
    return value


def _optional_time_horizon(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        if value.strip().lower() in _UNAVAILABLE_TOKENS:
            return None
        raise ComparisonValidationError("time_horizon must be a mapping with start and end")
    if not isinstance(value, Mapping):
        return None
    start = value.get("start")
    end = value.get("end")
    if not isinstance(start, str) or not isinstance(end, str):
        return None
    if start.strip().lower() in _UNAVAILABLE_TOKENS or end.strip().lower() in _UNAVAILABLE_TOKENS:
        return None
    if not _CREATED_AT_RE.fullmatch(start) or not _CREATED_AT_RE.fullmatch(end):
        raise ComparisonValidationError(
            "time_horizon.start/end must be UTC timestamps ending with Z"
        )
    if start >= end:
        raise ComparisonValidationError(
            "time_horizon.start must be strictly before time_horizon.end"
        )
    extra = set(str(key) for key in value.keys()) - {"start", "end"}
    if extra:
        raise ComparisonValidationError(f"time_horizon has unsupported keys: {sorted(extra)}")
    return compute_content_sha256(
        {
            "digest_algorithm": DIGEST_ALGORITHM,
            "digest_domain": f"{COMPARISON_DOMAIN}.time_horizon",
            "payload": {"end": end, "start": start},
            "schema_version": SCHEMA_VERSION,
        }
    )


def _optional_market_universe(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        if value.strip().lower() in _UNAVAILABLE_TOKENS:
            return None
        raise ComparisonValidationError(
            "market_universe must be a non-empty sequence of instruments"
        )
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    instruments: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            return None
        if item.strip().lower() in _UNAVAILABLE_TOKENS:
            return None
        if not _INSTRUMENT_RE.fullmatch(item):
            raise ComparisonValidationError(f"market_universe[{index}] is malformed")
        instruments.append(item)
    if not instruments:
        return None
    if len(set(instruments)) != len(instruments):
        raise ComparisonValidationError("market_universe cannot contain duplicate instruments")
    return compute_content_sha256(
        {
            "digest_algorithm": DIGEST_ALGORITHM,
            "digest_domain": f"{COMPARISON_DOMAIN}.market_universe",
            "payload": {"instruments": sorted(instruments)},
            "schema_version": SCHEMA_VERSION,
        }
    )


def _require_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ComparisonValidationError("experiment_identity present and valid is required")
    identity = _plain_mapping(value)
    try:
        validate_canonical_experiment_identity_v1(identity)
    except CanonicalExperimentIdentityError as exc:
        raise ComparisonValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    return identity


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise ComparisonValidationError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise ComparisonValidationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


def _require_token(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not _TOKEN_RE.fullmatch(value):
        raise ComparisonValidationError(f"{field_name} is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise ComparisonValidationError(f"{field_name} cannot use implicit unavailable tokens")
    return value


def _require_dimension(value: Any) -> str:
    dimension = _require_token("compatibility_rule.dimension", value)
    if dimension not in COMPARISON_DIMENSIONS:
        raise ComparisonValidationError(f"unknown comparison dimension: {dimension}")
    return dimension


def _require_comparison_value(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ComparisonValidationError(f"{field_name} must be a non-empty string")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise ComparisonValidationError(f"{field_name} cannot use implicit unavailable tokens")
    return value


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
    "COMPARISON_CONTRACT_VERSION",
    "COMPARISON_DIMENSIONS",
    "COMPARISON_DOMAIN",
    "COMPARISON_SSOT_CAN_PROMOTE",
    "COMPARISON_SSOT_CAN_RANK_NON_COMPARABLE",
    "COMPARISON_SSOT_HAS_RUNTIME_AUTHORITY",
    "CanonicalComparisonRankingRequestV1",
    "CanonicalComparisonRequestV1",
    "CHAMPION_CHALLENGER_IMPLEMENTED",
    "ComparisonCandidateV1",
    "ComparisonCompatibilityContractV1",
    "ComparisonRankingRejectedError",
    "ComparisonValidationError",
    "CompatibilityRuleV1",
    "OVERALL_COMPARABLE",
    "OVERALL_REJECTED",
    "PROMOTION_AUTHORITY",
    "RANKING_REASON_NON_COMPARABLE",
    "RANKING_STATUS_RANKED",
    "RANKING_STATUS_REJECTED",
    "SCHEMA_VERSION",
    "build_canonical_comparison_result_v1",
    "canonical_record_payload",
    "derive_comparison_identity_v1",
    "rank_comparable_candidates_v1",
    "validate_canonical_comparison_result_v1",
]
