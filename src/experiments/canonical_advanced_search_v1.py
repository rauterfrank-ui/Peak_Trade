"""Phase 12 Canonical Advanced Search v1 (research proposals only).

Enumerates a declared discrete search space, binds every candidate to
Phase 1 identity, consults Phase 3 / Phase 7 / Phase 11 signals, and
emits research candidates plus offline-experiment requests. This layer
does not rank, promote, write config, fund, or submit orders.
"""

from __future__ import annotations

import itertools
import logging
import math
import re
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityError,
    CanonicalExperimentIdentityRequestV1,
    canonicalize_mapping,
    build_canonical_experiment_identity_v1,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_failure_memory_v1 import (
    SCHEMA_VERSION as FAILURE_MEMORY_VERSION,
    assess_duplicate_hypothesis_v1,
    derive_hypothesis_fingerprint_v1,
    validate_canonical_failure_memory_record_v1,
)
from src.experiments.canonical_meta_learning_v1 import (
    CANONICAL_PROPOSAL_KINDS,
    META_LEARNING_AUTHORITY,
    PROPOSAL_DEPRIORITIZE_RESEARCH,
    PROPOSAL_INVESTIGATE,
    PROPOSAL_PRIORITIZE_RESEARCH,
    PROPOSAL_RETEST,
    PROMOTION_AUTHORITY as META_PROMOTION_AUTHORITY,
    SCHEMA_VERSION as META_LEARNING_SCHEMA_VERSION,
)
from src.experiments.canonical_reality_gap_store_v1 import (
    DISPOSITION_REJECTED_REALITY_GAP,
    SCHEMA_VERSION as REALITY_GAP_VERSION,
    validate_canonical_reality_gap_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    classify_patch_target,
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_advanced_search_v1"
ADVANCED_SEARCH_DOMAIN: Final[str] = "peak_trade.canonical_advanced_search.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
IDENTITY_SCHEMA_VERSION: Final[str] = "canonical_experiment_identity_v1"
EXPERIMENT_MEMORY_SCHEMA_VERSION: Final[str] = "canonical_experiment_memory_v1"
ROBUSTNESS_SUITE_VERSION: Final[str] = "canonical_robustness_suite_v1"
OFFLINE_LOOP_SCHEMA_VERSION: Final[str] = "canonical_automated_offline_research_loop_v1"
SEARCH_METHOD_VERSION: Final[str] = "canonical_advanced_search_method_v1"
OBJECTIVE_VERSION: Final[str] = "canonical_advanced_search_objective_v1"
CONSTRAINT_VERSION: Final[str] = "canonical_advanced_search_constraint_v1"
OBJECTIVE_ID: Final[str] = "SEARCH_PRIORITY_INFORMATION_GAIN_V1"
CONSTRAINT_ID: Final[str] = "SEARCH_AUTHORITY_AND_COST_INVARIANT_V1"

ADVANCED_SEARCH_PRESENT: Final[bool] = True
ADVANCED_SEARCH_AUTHORITY: Final[str] = "RESEARCH_ONLY"
SEARCH_IS_AUTHORITY_MECHANISM: Final[bool] = False
SEARCH_HAS_RUNTIME_AUTHORITY: Final[bool] = False
SEARCH_CAN_CREATE_RESEARCH_CANDIDATES: Final[bool] = True
SEARCH_CAN_CREATE_HYPOTHESES: Final[bool] = True
SEARCH_CAN_PROPOSE_PARAMETER_REGIONS: Final[bool] = True
SEARCH_CAN_USE_META_LEARNING_SIGNALS: Final[bool] = True
SEARCH_CAN_REQUEST_OFFLINE_EXPERIMENTS: Final[bool] = True
SEARCH_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
SEARCH_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
SEARCH_CAN_WRITE_TESTNET_CONFIG: Final[bool] = False
SEARCH_CAN_INCREASE_RISK: Final[bool] = False
SEARCH_CAN_INCREASE_LEVERAGE: Final[bool] = False
SEARCH_CAN_FUND: Final[bool] = False
SEARCH_CAN_SUBMIT_ORDER: Final[bool] = False
SEARCH_CAN_ARM: Final[bool] = False
SEARCH_CAN_ENABLE: Final[bool] = False
SEARCH_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
SEARCH_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
SEARCH_CAN_AUTHORIZE_CANARY: Final[bool] = False
SEARCH_CAN_PROMOTE: Final[bool] = False
SEARCH_CAN_PROMOTE_TO_LIVE: Final[bool] = False
SEARCH_CAN_REPLACE_PRODUCTIVE_CHAMPION: Final[bool] = False
SEARCH_CAN_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
AUTONOMOUS_CHAMPION_SWAP: Final[bool] = False
AUTONOMOUS_PROMOTION: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
SELF_LEARNING_NOT_SELF_AUTHORIZING: Final[bool] = True
HISTORICAL_RECORD_MUTATION: Final[bool] = False
PRODUCTIVE_CONFIG_MUTATION: Final[bool] = False
BEST_SHARPE_IS_NOT_AUTO_WINNER: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"
PHASE_13_STARTED: Final[bool] = False

SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH: Final[str] = (
    "BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH"
)
SUPPORTED_SEARCH_METHODS: Final[tuple[str, ...]] = (
    SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH,
)
UNSUPPORTED_SEARCH_METHODS: Final[tuple[str, ...]] = (
    "BAYESIAN_OPTIMIZATION",
    "OPTUNA",
    "EVOLUTIONARY_SEARCH",
    "GENETIC_ALGORITHM",
    "ML_BASED_SEARCH",
    "AGENTIC_HYPOTHESIS_GENERATION",
    "REINFORCEMENT_LEARNING",
)

LINEAGE_KIND_ROOT: Final[str] = "ROOT"
LINEAGE_KIND_PARENT_BOUND: Final[str] = "PARENT_BOUND"
CANONICAL_LINEAGE_KINDS: Final[tuple[str, ...]] = (LINEAGE_KIND_ROOT, LINEAGE_KIND_PARENT_BOUND)

STATUS_PROPOSED: Final[str] = "PROPOSED"
STATUS_BUDGET_EXCLUDED: Final[str] = "BUDGET_EXCLUDED"
STATUS_DEPRIORITIZED_KNOWN_FAILURE: Final[str] = "DEPRIORITIZED_KNOWN_FAILURE"
STATUS_REJECTED_DUPLICATE_WITHOUT_RETEST: Final[str] = "REJECTED_DUPLICATE_WITHOUT_RETEST"
STATUS_REJECTED_IDENTITY: Final[str] = "REJECTED_IDENTITY"
STATUS_REJECTED_CONSTRAINT: Final[str] = "REJECTED_CONSTRAINT"
CANONICAL_CANDIDATE_STATUSES: Final[tuple[str, ...]] = (
    STATUS_PROPOSED,
    STATUS_BUDGET_EXCLUDED,
    STATUS_DEPRIORITIZED_KNOWN_FAILURE,
    STATUS_REJECTED_DUPLICATE_WITHOUT_RETEST,
    STATUS_REJECTED_IDENTITY,
    STATUS_REJECTED_CONSTRAINT,
)
OVERALL_COMPLETE: Final[str] = "SEARCH_COMPLETE"
OFFLINE_REQUEST_KIND: Final[str] = "OFFLINE_EXPERIMENT_REQUEST"

ROBUSTNESS_FAILURE_CLASSES: Final[frozenset[str]] = frozenset(
    {
        "REJECTED_OVERFIT",
        "REJECTED_TAIL_RISK",
        "REJECTED_COST_SENSITIVITY",
        "REJECTED_REGIME_CONCENTRATION",
        "REJECTED_DATA_QUALITY",
        "REJECTED_REPRODUCIBILITY",
    }
)
FROZEN_IDENTITY_FIELDS: Final[tuple[str, ...]] = (
    "bull_bear_logic_digest",
    "cost_model_digest",
    "dataset_digest",
    "double_play_logic_digest",
    "entry_position_exit_logic_digest",
    "environment_digest",
    "feature_pipeline_digest",
    "fee_model_digest",
    "funding_model_digest",
    "git_sha",
    "market_context_contract_digest",
    "portfolio_digest",
    "risk_policy_digest",
    "seed",
    "slippage_model_digest",
    "split_policy_digest",
    "state_switch_logic_digest",
    "strategy_identity",
    "suitability_logic_digest",
    "survival_logic_digest",
    "trading_decision_core_digest",
    "working_tree_status",
)
FORBIDDEN_SEARCH_AXIS_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "arm",
        "armed",
        "canary",
        "capital",
        "champion",
        "confirm_token",
        "dataset",
        "enable",
        "enabled",
        "execution",
        "fee",
        "fees",
        "fill",
        "fund",
        "funding",
        "holdout",
        "kill_switch",
        "leverage",
        "liquidity",
        "live",
        "order",
        "orders",
        "promotion",
        "risk",
        "routing",
        "sizing",
        "slippage",
        "split",
        "stop",
        "tail",
        "tail_risk",
        "testnet",
        "turnover",
    }
)
PRIORITY_PRIORITIZE: Final[int] = 20
PRIORITY_INVESTIGATE: Final[int] = 10
PRIORITY_NEUTRAL: Final[int] = 0
PRIORITY_DEPRIORITIZE: Final[int] = -20
PRIORITY_DUPLICATE_WARN: Final[int] = -5

_CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_AXIS_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
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

_LOGGER = logging.getLogger(__name__)


class AdvancedSearchValidationError(ValueError):
    """Fail-closed Canonical Advanced Search v1 validation error."""


@dataclass(frozen=True)
class SearchAxisV1:
    name: str
    values: Sequence[Any]


@dataclass(frozen=True)
class SearchSpaceV1:
    search_space_id: str
    axes: Sequence[SearchAxisV1]


@dataclass(frozen=True)
class SearchObjectiveV1:
    objective_id: str
    objective_version: str
    sharpe_is_not_auto_winner: bool
    search_score_is_not_canonical_ranking: bool


@dataclass(frozen=True)
class SearchConstraintV1:
    constraint_id: str
    constraint_version: str
    cannot_increase_risk: bool
    cannot_increase_leverage: bool
    cannot_write_live_config: bool
    cannot_write_testnet_config: bool
    cannot_submit_order: bool
    cannot_fund: bool
    cannot_arm: bool
    cannot_enable: bool
    cannot_create_or_use_confirm_token: bool
    cannot_authorize_canary: bool
    cannot_promote: bool
    search_score_is_not_canonical_ranking: bool


@dataclass(frozen=True)
class CanonicalAdvancedSearchRequestV1:
    identity_template: CanonicalExperimentIdentityRequestV1
    search_space: SearchSpaceV1
    search_method: str
    search_method_version: str
    seed: int
    budget: int
    search_space_cardinality_limit: int
    objective: SearchObjectiveV1
    constraint: SearchConstraintV1
    created_at: str
    parent_hypothesis_id: str
    lineage_kind: str
    hypothesis_kind: str
    strategy_family: str
    regime: str
    robustness_policy_digest: str
    parent_experiment_identity: Mapping[str, Any] | None = None
    failure_records: Sequence[Mapping[str, Any]] = ()
    reality_gap_records: Sequence[Mapping[str, Any]] = ()
    meta_learning_signals: Sequence[Mapping[str, Any]] = ()
    meta_learning_identity: str | None = None
    retest_reason: str | None = None


def canonical_advanced_search_objective_v1() -> SearchObjectiveV1:
    return SearchObjectiveV1(
        objective_id=OBJECTIVE_ID,
        objective_version=OBJECTIVE_VERSION,
        sharpe_is_not_auto_winner=True,
        search_score_is_not_canonical_ranking=True,
    )


def canonical_advanced_search_constraint_v1() -> SearchConstraintV1:
    return SearchConstraintV1(
        constraint_id=CONSTRAINT_ID,
        constraint_version=CONSTRAINT_VERSION,
        cannot_increase_risk=True,
        cannot_increase_leverage=True,
        cannot_write_live_config=True,
        cannot_write_testnet_config=True,
        cannot_submit_order=True,
        cannot_fund=True,
        cannot_arm=True,
        cannot_enable=True,
        cannot_create_or_use_confirm_token=True,
        cannot_authorize_canary=True,
        cannot_promote=True,
        search_score_is_not_canonical_ranking=True,
    )


def build_canonical_advanced_search_v1(
    request: CanonicalAdvancedSearchRequestV1,
) -> Mapping[str, Any]:
    created_at = _require_created_at(request.created_at)
    search_method = _require_search_method(request.search_method)
    search_method_version = _require_token("search_method_version", request.search_method_version)
    if search_method_version != SEARCH_METHOD_VERSION:
        raise AdvancedSearchValidationError("search_method_version mismatch")
    seed = _require_seed(request.seed)
    budget = _require_positive_int("budget", request.budget)
    cardinality_limit = _require_positive_int(
        "search_space_cardinality_limit", request.search_space_cardinality_limit
    )
    objective = _canonicalize_objective(request.objective)
    constraint = _canonicalize_constraint(request.constraint)
    parent_hypothesis_id = _require_token("parent_hypothesis_id", request.parent_hypothesis_id)
    lineage_kind = _require_enum("lineage_kind", request.lineage_kind, CANONICAL_LINEAGE_KINDS)
    hypothesis_kind = _require_token("hypothesis_kind", request.hypothesis_kind)
    strategy_family = _require_token("strategy_family", request.strategy_family)
    regime = _require_token("regime", request.regime)
    robustness_policy_digest = _require_sha256(
        "robustness_policy_digest", request.robustness_policy_digest
    )
    retest_reason = _optional_retest_reason(request.retest_reason)
    search_space, search_space_digest, combinations = _canonicalize_search_space(
        request.search_space, cardinality_limit=cardinality_limit
    )
    template_identity = _build_template_identity(request.identity_template)
    parent_identity = _canonicalize_parent_identity(
        request.parent_experiment_identity, lineage_kind=lineage_kind
    )
    failure_records = _canonicalize_failure_records(
        request.failure_records, template_identity=template_identity
    )
    gap_records = _canonicalize_gap_records(
        request.reality_gap_records, template_identity=template_identity
    )
    meta_signals = _canonicalize_meta_signals(
        request.meta_learning_signals,
        meta_learning_identity=request.meta_learning_identity,
    )
    candidates = [
        _evaluate_combination(
            combination,
            identity_template=request.identity_template,
            template_identity=template_identity,
            parent_identity=parent_identity,
            lineage_kind=lineage_kind,
            parent_hypothesis_id=parent_hypothesis_id,
            hypothesis_kind=hypothesis_kind,
            strategy_family=strategy_family,
            regime=regime,
            robustness_policy_digest=robustness_policy_digest,
            search_space_id=str(search_space["search_space_id"]),
            failure_records=failure_records,
            gap_records=gap_records,
            meta_signals=meta_signals,
            retest_reason=retest_reason,
        )
        for combination in combinations
    ]
    _assign_proposal_budget(candidates, budget=budget)
    proposed = [item for item in candidates if item["status"] == STATUS_PROPOSED]
    hypotheses = [_hypothesis_projection(item) for item in proposed]
    parameter_region_proposals = [
        {
            "hypothesis_id": item["hypothesis_id"],
            "parameter_region": item["parameter_region"],
            "status": item["status"],
        }
        for item in candidates
    ]
    offline_experiment_requests = [
        item["offline_experiment_request"]
        for item in proposed
        if item["offline_experiment_request"] is not None
    ]
    input_lineage = {
        "contract_versions": {
            "advanced_search": SCHEMA_VERSION,
            "experiment_identity": IDENTITY_SCHEMA_VERSION,
            "experiment_memory": EXPERIMENT_MEMORY_SCHEMA_VERSION,
            "failure_memory": FAILURE_MEMORY_VERSION,
            "meta_learning": META_LEARNING_SCHEMA_VERSION,
            "offline_research_loop": OFFLINE_LOOP_SCHEMA_VERSION,
            "reality_gap_store": REALITY_GAP_VERSION,
            "robustness_suite": ROBUSTNESS_SUITE_VERSION,
        },
        "failure_record_ids": [item["failure_record_id"] for item in failure_records],
        "generated_candidate_refs": [item["candidate_ref"] for item in candidates],
        "identity_digest": template_identity["identity_digest"],
        "meta_learning_identity": request.meta_learning_identity,
        "parent_experiment_id": (
            derive_experiment_id_v1(str(parent_identity["identity_digest"]))
            if parent_identity is not None
            else None
        ),
        "parent_hypothesis_id": parent_hypothesis_id,
        "reality_gap_record_ids": [item["reality_gap_record_id"] for item in gap_records],
    }
    body = {
        "advanced_search_authority": ADVANCED_SEARCH_AUTHORITY,
        "advanced_search_domain": ADVANCED_SEARCH_DOMAIN,
        "advanced_search_present": ADVANCED_SEARCH_PRESENT,
        "autonomous_champion_swap": AUTONOMOUS_CHAMPION_SWAP,
        "autonomous_promotion": AUTONOMOUS_PROMOTION,
        "best_sharpe_is_not_auto_winner": BEST_SHARPE_IS_NOT_AUTO_WINNER,
        "budget": budget,
        "candidates": candidates,
        "champion_experiment_id": None,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "constraint": constraint,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "duplicate_assessments": [item["duplicate_assessment"] for item in candidates],
        "historical_record_mutation": HISTORICAL_RECORD_MUTATION,
        "hypotheses": hypotheses,
        "input_lineage": input_lineage,
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "objective": objective,
        "offline_experiment_requests": offline_experiment_requests,
        "overall_status": OVERALL_COMPLETE,
        "parameter_region_proposals": parameter_region_proposals,
        "phase_13_started": PHASE_13_STARTED,
        "productive_config_mutation": PRODUCTIVE_CONFIG_MUTATION,
        "promotion_authority": PROMOTION_AUTHORITY,
        "ranked_experiment_ids": [],
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "search_can_arm": SEARCH_CAN_ARM,
        "search_can_authorize_canary": SEARCH_CAN_AUTHORIZE_CANARY,
        "search_can_autonomously_replace_core_logic": (SEARCH_CAN_AUTONOMOUSLY_REPLACE_CORE_LOGIC),
        "search_can_create_confirm_token": SEARCH_CAN_CREATE_CONFIRM_TOKEN,
        "search_can_create_hypotheses": SEARCH_CAN_CREATE_HYPOTHESES,
        "search_can_create_research_candidates": SEARCH_CAN_CREATE_RESEARCH_CANDIDATES,
        "search_can_enable": SEARCH_CAN_ENABLE,
        "search_can_fund": SEARCH_CAN_FUND,
        "search_can_increase_leverage": SEARCH_CAN_INCREASE_LEVERAGE,
        "search_can_increase_risk": SEARCH_CAN_INCREASE_RISK,
        "search_can_mutate_live_config": SEARCH_CAN_MUTATE_LIVE_CONFIG,
        "search_can_promote": SEARCH_CAN_PROMOTE,
        "search_can_promote_to_live": SEARCH_CAN_PROMOTE_TO_LIVE,
        "search_can_propose_parameter_regions": SEARCH_CAN_PROPOSE_PARAMETER_REGIONS,
        "search_can_replace_productive_champion": SEARCH_CAN_REPLACE_PRODUCTIVE_CHAMPION,
        "search_can_request_offline_experiments": SEARCH_CAN_REQUEST_OFFLINE_EXPERIMENTS,
        "search_can_submit_order": SEARCH_CAN_SUBMIT_ORDER,
        "search_can_use_confirm_token": SEARCH_CAN_USE_CONFIRM_TOKEN,
        "search_can_use_meta_learning_signals": SEARCH_CAN_USE_META_LEARNING_SIGNALS,
        "search_can_write_live_config": SEARCH_CAN_WRITE_LIVE_CONFIG,
        "search_can_write_testnet_config": SEARCH_CAN_WRITE_TESTNET_CONFIG,
        "search_evidence": {
            "candidate_count": len(candidates),
            "deprioritized_known_failure_count": _count_status(
                candidates, STATUS_DEPRIORITIZED_KNOWN_FAILURE
            ),
            "proposed_count": len(proposed),
            "rejected_constraint_count": _count_status(candidates, STATUS_REJECTED_CONSTRAINT),
            "rejected_duplicate_count": _count_status(
                candidates, STATUS_REJECTED_DUPLICATE_WITHOUT_RETEST
            ),
            "rejected_identity_count": _count_status(candidates, STATUS_REJECTED_IDENTITY),
            "search_score_is_not_canonical_ranking": True,
        },
        "search_has_runtime_authority": SEARCH_HAS_RUNTIME_AUTHORITY,
        "search_is_authority_mechanism": SEARCH_IS_AUTHORITY_MECHANISM,
        "search_method": search_method,
        "search_method_version": search_method_version,
        "search_space": search_space,
        "search_space_digest": search_space_digest,
        "seed": seed,
        "self_learning_not_self_authorizing": SELF_LEARNING_NOT_SELF_AUTHORIZING,
        "self_learning_self_authorizing_separation": SELF_LEARNING_SELF_AUTHORIZING_SEPARATION,
        "supported_search_mechanisms": list(SUPPORTED_SEARCH_METHODS),
    }
    search_identity = derive_search_identity_v1(body)
    record = dict(body)
    record["search_identity"] = search_identity
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_advanced_search_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_advanced_search_v1 built identity=%s proposed=%s authority=%s",
        search_identity,
        len(proposed),
        ADVANCED_SEARCH_AUTHORITY,
    )
    return frozen


def derive_search_identity_v1(record_without_ids: Mapping[str, Any]) -> str:
    payload = {
        key: value
        for key, value in _plain_mapping(record_without_ids).items()
        if key not in {"search_identity", "integrity"}
    }
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{ADVANCED_SEARCH_DOMAIN}.search_identity",
        "payload": payload,
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def canonical_record_payload_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def validate_canonical_advanced_search_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise AdvancedSearchValidationError("advanced-search record must be a mapping")
    payload = _plain_mapping(record)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise AdvancedSearchValidationError("schema_version mismatch")
    if payload.get("advanced_search_domain") != ADVANCED_SEARCH_DOMAIN:
        raise AdvancedSearchValidationError("advanced_search_domain mismatch")
    if payload.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise AdvancedSearchValidationError("non-COMPLETE advanced-search records are forbidden")
    if payload.get("advanced_search_authority") != ADVANCED_SEARCH_AUTHORITY:
        raise AdvancedSearchValidationError("advanced_search_authority must be RESEARCH_ONLY")
    if payload.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise AdvancedSearchValidationError("promotion_authority must be NONE")
    if payload.get("search_is_authority_mechanism") is not False:
        raise AdvancedSearchValidationError("search_is_authority_mechanism must be false")
    if payload.get("search_has_runtime_authority") is not False:
        raise AdvancedSearchValidationError("search_has_runtime_authority must be false")
    if payload.get("ranked_experiment_ids") != []:
        raise AdvancedSearchValidationError("ranked_experiment_ids must remain empty")
    if payload.get("champion_experiment_id") is not None:
        raise AdvancedSearchValidationError("champion_experiment_id must be null")
    if payload.get("phase_13_started") is not False:
        raise AdvancedSearchValidationError("phase_13_started must be false")
    if payload.get("historical_record_mutation") is not False:
        raise AdvancedSearchValidationError("historical_record_mutation must be false")
    if payload.get("productive_config_mutation") is not False:
        raise AdvancedSearchValidationError("productive_config_mutation must be false")
    if payload.get("best_sharpe_is_not_auto_winner") is not True:
        raise AdvancedSearchValidationError("best_sharpe_is_not_auto_winner must be true")
    if payload.get("search_method") not in SUPPORTED_SEARCH_METHODS:
        raise AdvancedSearchValidationError("unsupported search_method")
    if payload.get("search_can_promote") is not False:
        raise AdvancedSearchValidationError("search_can_promote must be false")
    if payload.get("search_can_write_live_config") is not False:
        raise AdvancedSearchValidationError("search_can_write_live_config must be false")
    if payload.get("search_can_increase_risk") is not False:
        raise AdvancedSearchValidationError("search_can_increase_risk must be false")
    if payload.get("search_can_increase_leverage") is not False:
        raise AdvancedSearchValidationError("search_can_increase_leverage must be false")
    if payload.get("search_can_submit_order") is not False:
        raise AdvancedSearchValidationError("search_can_submit_order must be false")
    if payload.get("search_can_fund") is not False:
        raise AdvancedSearchValidationError("search_can_fund must be false")
    if payload.get("search_can_authorize_canary") is not False:
        raise AdvancedSearchValidationError("search_can_authorize_canary must be false")
    if payload.get("search_can_create_confirm_token") is not False:
        raise AdvancedSearchValidationError("search_can_create_confirm_token must be false")
    if payload.get("search_can_use_confirm_token") is not False:
        raise AdvancedSearchValidationError("search_can_use_confirm_token must be false")
    if payload.get("search_can_autonomously_replace_core_logic") is not False:
        raise AdvancedSearchValidationError(
            "search_can_autonomously_replace_core_logic must be false"
        )
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise AdvancedSearchValidationError("candidates must be a non-empty list")
    for candidate in candidates:
        if candidate.get("status") not in CANONICAL_CANDIDATE_STATUSES:
            raise AdvancedSearchValidationError("candidate status is not canonical")
        if candidate.get("search_score_is_not_canonical_ranking") is not True:
            raise AdvancedSearchValidationError(
                "search_score_is_not_canonical_ranking must be true"
            )
        if candidate.get("status") == STATUS_PROPOSED:
            if candidate.get("offline_experiment_request") is None:
                raise AdvancedSearchValidationError(
                    "proposed candidates must request an offline experiment"
                )
            if candidate.get("offline_experiment_request", {}).get("executed") is not False:
                raise AdvancedSearchValidationError("offline experiment request must not execute")
            if candidate.get("offline_experiment_request", {}).get("loop_started") is not False:
                raise AdvancedSearchValidationError(
                    "offline experiment request must not start loop"
                )
        else:
            if candidate.get("offline_experiment_request") is not None:
                raise AdvancedSearchValidationError(
                    "non-proposed candidates must not request offline experiments"
                )
    expected_identity = derive_search_identity_v1(
        {key: value for key, value in payload.items() if key != "integrity"}
    )
    if payload.get("search_identity") != expected_identity:
        raise AdvancedSearchValidationError("search_identity is not bound to canonical content")
    expected_integrity = compute_content_sha256(
        {key: value for key, value in payload.items() if key != "integrity"}
    )
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise AdvancedSearchValidationError("integrity.content_sha256 mismatch")


def _evaluate_combination(
    combination: Mapping[str, Any],
    *,
    identity_template: CanonicalExperimentIdentityRequestV1,
    template_identity: Mapping[str, Any],
    parent_identity: Mapping[str, Any] | None,
    lineage_kind: str,
    parent_hypothesis_id: str,
    hypothesis_kind: str,
    strategy_family: str,
    regime: str,
    robustness_policy_digest: str,
    search_space_id: str,
    failure_records: Sequence[Mapping[str, Any]],
    gap_records: Sequence[Mapping[str, Any]],
    meta_signals: Sequence[Mapping[str, Any]],
    retest_reason: str | None,
) -> dict[str, Any]:
    parameter_region = canonicalize_mapping(combination)
    hypothesis_id = _candidate_hypothesis_id(parent_hypothesis_id, parameter_region)
    constraint_reason = _constraint_violation(parameter_region)
    if constraint_reason is not None:
        return _rejected_candidate(
            hypothesis_id=hypothesis_id,
            parameter_region=parameter_region,
            status=STATUS_REJECTED_CONSTRAINT,
            reason=constraint_reason,
            search_space_id=search_space_id,
            hypothesis_kind=hypothesis_kind,
            strategy_family=strategy_family,
        )
    try:
        candidate_identity = _bind_candidate_identity(
            identity_template,
            parameter_region=parameter_region,
            parent_identity=parent_identity,
            lineage_kind=lineage_kind,
        )
        _assert_frozen_identity(template_identity, candidate_identity)
    except (AdvancedSearchValidationError, CanonicalExperimentIdentityError) as exc:
        return _rejected_candidate(
            hypothesis_id=hypothesis_id,
            parameter_region=parameter_region,
            status=STATUS_REJECTED_IDENTITY,
            reason=str(exc),
            search_space_id=search_space_id,
            hypothesis_kind=hypothesis_kind,
            strategy_family=strategy_family,
        )
    experiment_id = derive_experiment_id_v1(str(candidate_identity["identity_digest"]))
    parent_lineage_ref = _parent_lineage_ref(candidate_identity)
    fingerprint = derive_hypothesis_fingerprint_v1(
        identity_digest=str(candidate_identity["identity_digest"]),
        hypothesis_id=hypothesis_id,
        parameter_region=parameter_region,
        regime=regime,
        robustness_policy_digest=robustness_policy_digest,
        parent_lineage_ref=parent_lineage_ref,
    )
    duplicate_assessment = _plain_mapping(
        assess_duplicate_hypothesis_v1(
            failure_records,
            hypothesis_fingerprint=fingerprint,
            parameter_region=parameter_region,
        )
    )
    failure_signals = _failure_signals(
        failure_records,
        gap_records=gap_records,
        parameter_region=parameter_region,
        identity=candidate_identity,
    )
    if (
        duplicate_assessment.get("detected") is True
        and "REQUIRE_EXPLICIT_RETEST_REASON" in duplicate_assessment.get("actions", [])
        and retest_reason is None
    ):
        return _candidate_body(
            hypothesis_id=hypothesis_id,
            parameter_region=parameter_region,
            status=STATUS_REJECTED_DUPLICATE_WITHOUT_RETEST,
            reason="duplicate hypothesis requires an explicit retest_reason",
            search_space_id=search_space_id,
            hypothesis_kind=hypothesis_kind,
            strategy_family=strategy_family,
            identity=candidate_identity,
            experiment_id=experiment_id,
            fingerprint=fingerprint,
            duplicate_assessment=duplicate_assessment,
            failure_signals=failure_signals,
            priority_score=PRIORITY_NEUTRAL,
            matched_signals=(),
        )
    if failure_signals["known_failure"] and retest_reason is None:
        return _candidate_body(
            hypothesis_id=hypothesis_id,
            parameter_region=parameter_region,
            status=STATUS_DEPRIORITIZED_KNOWN_FAILURE,
            reason=str(failure_signals["reason"]),
            search_space_id=search_space_id,
            hypothesis_kind=hypothesis_kind,
            strategy_family=strategy_family,
            identity=candidate_identity,
            experiment_id=experiment_id,
            fingerprint=fingerprint,
            duplicate_assessment=duplicate_assessment,
            failure_signals=failure_signals,
            priority_score=PRIORITY_DEPRIORITIZE,
            matched_signals=(),
        )
    matched_signals, priority_score = _priority_from_signals(
        meta_signals,
        strategy_family=strategy_family,
        search_space_id=search_space_id,
        hypothesis_kind=hypothesis_kind,
        parameter_region=parameter_region,
        duplicate_assessment=duplicate_assessment,
    )
    return _candidate_body(
        hypothesis_id=hypothesis_id,
        parameter_region=parameter_region,
        status=STATUS_PROPOSED,
        reason="eligible research candidate",
        search_space_id=search_space_id,
        hypothesis_kind=hypothesis_kind,
        strategy_family=strategy_family,
        identity=candidate_identity,
        experiment_id=experiment_id,
        fingerprint=fingerprint,
        duplicate_assessment=duplicate_assessment,
        failure_signals=failure_signals,
        priority_score=priority_score,
        matched_signals=matched_signals,
        offline_experiment_request=_offline_request(
            hypothesis_id=hypothesis_id,
            experiment_id=experiment_id,
            identity_digest=str(candidate_identity["identity_digest"]),
            parameter_region=parameter_region,
            regime=regime,
        ),
    )


def _assign_proposal_budget(candidates: list[dict[str, Any]], *, budget: int) -> None:
    eligible = [item for item in candidates if item["status"] == STATUS_PROPOSED]
    eligible.sort(
        key=lambda item: (-int(item["search_priority_score"]), str(item["hypothesis_id"]))
    )
    for index, item in enumerate(eligible):
        if index < budget:
            continue
        item["status"] = STATUS_BUDGET_EXCLUDED
        item["reason"] = "eligible candidate excluded by explicit search budget"
        item["offline_experiment_request"] = None


def _bind_candidate_identity(
    template: CanonicalExperimentIdentityRequestV1,
    *,
    parameter_region: Mapping[str, Any],
    parent_identity: Mapping[str, Any] | None,
    lineage_kind: str,
) -> Mapping[str, Any]:
    template_params = canonicalize_mapping(template.strategy_params)
    missing = [key for key in parameter_region if key not in template_params]
    if missing:
        raise AdvancedSearchValidationError(
            f"search axes are not bound on the identity template: {sorted(missing)}"
        )
    strategy_params = dict(template_params)
    strategy_params.update(parameter_region)
    parent_lineage_ref = template.parent_lineage_ref
    if lineage_kind == LINEAGE_KIND_PARENT_BOUND:
        assert parent_identity is not None
        parent_lineage_ref = str(parent_identity["identity_digest"])
    request = replace(
        template,
        strategy_params=strategy_params,
        parent_lineage_ref=parent_lineage_ref,
    )
    identity = build_canonical_experiment_identity_v1(request)
    validate_canonical_experiment_identity_v1(identity)
    return _plain_mapping(identity)


def _build_template_identity(
    template: CanonicalExperimentIdentityRequestV1,
) -> dict[str, Any]:
    try:
        identity = build_canonical_experiment_identity_v1(template)
    except CanonicalExperimentIdentityError as exc:
        raise AdvancedSearchValidationError(
            f"identity template is not a COMPLETE Canonical Experiment Identity: {exc}"
        ) from exc
    validate_canonical_experiment_identity_v1(identity)
    _reject_forbidden_param_keys("identity_template.strategy_params", template.strategy_params)
    return _plain_mapping(identity)


def _assert_frozen_identity(
    template_identity: Mapping[str, Any], candidate_identity: Mapping[str, Any]
) -> None:
    for field_name in FROZEN_IDENTITY_FIELDS:
        if template_identity.get(field_name) != candidate_identity.get(field_name):
            raise AdvancedSearchValidationError(
                f"search mutated frozen identity field {field_name}"
            )


def _canonicalize_search_space(
    space: SearchSpaceV1, *, cardinality_limit: int
) -> tuple[dict[str, Any], str, list[dict[str, Any]]]:
    search_space_id = _require_token("search_space_id", space.search_space_id)
    if not isinstance(space.axes, Sequence) or isinstance(space.axes, (str, bytes)):
        raise AdvancedSearchValidationError("search_space.axes must be a sequence")
    if not space.axes:
        raise AdvancedSearchValidationError("search_space.axes must not be empty")
    axes: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    value_lists: list[list[Any]] = []
    names: list[str] = []
    for index, axis in enumerate(space.axes):
        if not isinstance(axis, SearchAxisV1):
            raise AdvancedSearchValidationError(f"search_space.axes[{index}] must be SearchAxisV1")
        name = _require_axis_name(axis.name)
        if name in seen_names:
            raise AdvancedSearchValidationError(f"duplicate search axis: {name}")
        seen_names.add(name)
        values = _canonicalize_axis_values(name, axis.values)
        axes.append({"name": name, "values": values})
        names.append(name)
        value_lists.append(values)
    axes.sort(key=lambda item: str(item["name"]))
    names = [str(item["name"]) for item in axes]
    value_lists = [list(item["values"]) for item in axes]
    product = list(itertools.product(*value_lists))
    if not product:
        raise AdvancedSearchValidationError("search space produced no combinations")
    if len(product) > cardinality_limit:
        raise AdvancedSearchValidationError(
            "search space cardinality exceeds search_space_cardinality_limit"
        )
    combinations = [
        {name: value for name, value in zip(names, row, strict=True)} for row in product
    ]
    combinations.sort(key=lambda item: tuple((key, repr(item[key])) for key in names))
    payload = {"axes": axes, "search_space_id": search_space_id}
    digest = compute_content_sha256(
        {
            "digest_algorithm": DIGEST_ALGORITHM,
            "digest_domain": f"{ADVANCED_SEARCH_DOMAIN}.search_space",
            "payload": payload,
            "schema_version": SCHEMA_VERSION,
        }
    )
    return payload, digest, combinations


def _canonicalize_axis_values(name: str, values: Sequence[Any]) -> list[Any]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise AdvancedSearchValidationError(f"search axis {name} values must be a sequence")
    if not values:
        raise AdvancedSearchValidationError(f"search axis {name} values must not be empty")
    canonical: list[Any] = []
    seen: set[str] = set()
    for value in values:
        item = _canonicalize_axis_value(name, value)
        marker = repr(item)
        if marker in seen:
            raise AdvancedSearchValidationError(f"search axis {name} has duplicate values")
        seen.add(marker)
        canonical.append(item)
    return canonical


def _canonicalize_axis_value(name: str, value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        raise AdvancedSearchValidationError(f"search axis {name} values must not be bool or null")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AdvancedSearchValidationError(f"search axis {name} values must be finite")
        return value
    if isinstance(value, str):
        return _require_token(f"search axis {name} value", value)
    raise AdvancedSearchValidationError(
        f"search axis {name} values must be int, finite float, or canonical tokens"
    )


def _require_axis_name(value: Any) -> str:
    name = _require_token("search axis name", value)
    if _AXIS_NAME_RE.fullmatch(name) is None:
        raise AdvancedSearchValidationError(f"search axis name is not canonical: {name}")
    _reject_forbidden_param_keys("search axis", {name: True})
    allowed, reason = classify_patch_target(name)
    if not allowed:
        raise AdvancedSearchValidationError(f"search axis is a forbidden surface: {reason}")
    return name


def _reject_forbidden_param_keys(field_name: str, payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise AdvancedSearchValidationError(f"{field_name} must be a mapping")
    for raw_key in payload:
        key = str(raw_key).strip().lower()
        normalized = key.replace("-", "_")
        if normalized in FORBIDDEN_SEARCH_AXIS_TOKENS:
            raise AdvancedSearchValidationError(
                f"{field_name} contains forbidden search dimension {raw_key}"
            )
        for token in FORBIDDEN_SEARCH_AXIS_TOKENS:
            if (
                normalized == token
                or normalized.startswith(f"{token}_")
                or f"_{token}_" in (f"_{normalized}_")
            ):
                raise AdvancedSearchValidationError(
                    f"{field_name} contains forbidden search dimension {raw_key}"
                )


def _constraint_violation(parameter_region: Mapping[str, Any]) -> str | None:
    try:
        _reject_forbidden_param_keys("parameter_region", parameter_region)
    except AdvancedSearchValidationError as exc:
        return str(exc)
    return None


def _canonicalize_objective(objective: SearchObjectiveV1) -> dict[str, Any]:
    if objective.objective_id != OBJECTIVE_ID:
        raise AdvancedSearchValidationError("objective_id mismatch")
    if objective.objective_version != OBJECTIVE_VERSION:
        raise AdvancedSearchValidationError("objective_version mismatch")
    if objective.sharpe_is_not_auto_winner is not True:
        raise AdvancedSearchValidationError("sharpe_is_not_auto_winner must be true")
    if objective.search_score_is_not_canonical_ranking is not True:
        raise AdvancedSearchValidationError("search_score_is_not_canonical_ranking must be true")
    return {
        "objective_id": OBJECTIVE_ID,
        "objective_version": OBJECTIVE_VERSION,
        "search_score_is_not_canonical_ranking": True,
        "sharpe_is_not_auto_winner": True,
    }


def _canonicalize_constraint(constraint: SearchConstraintV1) -> dict[str, Any]:
    if constraint.constraint_id != CONSTRAINT_ID:
        raise AdvancedSearchValidationError("constraint_id mismatch")
    if constraint.constraint_version != CONSTRAINT_VERSION:
        raise AdvancedSearchValidationError("constraint_version mismatch")
    required_true = (
        "cannot_increase_risk",
        "cannot_increase_leverage",
        "cannot_write_live_config",
        "cannot_write_testnet_config",
        "cannot_submit_order",
        "cannot_fund",
        "cannot_arm",
        "cannot_enable",
        "cannot_create_or_use_confirm_token",
        "cannot_authorize_canary",
        "cannot_promote",
        "search_score_is_not_canonical_ranking",
    )
    payload = {name: getattr(constraint, name) for name in required_true}
    for name, value in payload.items():
        if value is not True:
            raise AdvancedSearchValidationError(f"{name} must be true")
    return {
        "cannot_arm": True,
        "cannot_authorize_canary": True,
        "cannot_create_or_use_confirm_token": True,
        "cannot_enable": True,
        "cannot_fund": True,
        "cannot_increase_leverage": True,
        "cannot_increase_risk": True,
        "cannot_promote": True,
        "cannot_submit_order": True,
        "cannot_write_live_config": True,
        "cannot_write_testnet_config": True,
        "constraint_id": CONSTRAINT_ID,
        "constraint_version": CONSTRAINT_VERSION,
        "search_score_is_not_canonical_ranking": True,
    }


def _canonicalize_parent_identity(
    value: Mapping[str, Any] | None, *, lineage_kind: str
) -> dict[str, Any] | None:
    if lineage_kind == LINEAGE_KIND_ROOT:
        if value is not None:
            raise AdvancedSearchValidationError(
                "ROOT search must not supply parent_experiment_identity"
            )
        return None
    if value is None:
        raise AdvancedSearchValidationError(
            "PARENT_BOUND search requires parent_experiment_identity"
        )
    validate_canonical_experiment_identity_v1(value)
    return _plain_mapping(value)


def _canonicalize_failure_records(
    records: Sequence[Mapping[str, Any]], *, template_identity: Mapping[str, Any]
) -> list[dict[str, Any]]:
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise AdvancedSearchValidationError("failure_records must be a sequence")
    bound: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(records):
        try:
            validate_canonical_failure_memory_record_v1(item)
        except Exception as exc:
            raise AdvancedSearchValidationError(
                f"failure_records[{index}] is not a COMPLETE Phase 3 record"
            ) from exc
        payload = _plain_mapping(item)
        _assert_signal_identity_compatible(
            template_identity,
            payload["experiment_identity"],
            field_name=f"failure_records[{index}]",
        )
        record_id = str(payload["failure_record_id"])
        if record_id in seen:
            raise AdvancedSearchValidationError("duplicate failure_record_id")
        seen.add(record_id)
        bound.append(payload)
    bound.sort(key=lambda item: str(item["failure_record_id"]))
    return bound


def _canonicalize_gap_records(
    records: Sequence[Mapping[str, Any]], *, template_identity: Mapping[str, Any]
) -> list[dict[str, Any]]:
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise AdvancedSearchValidationError("reality_gap_records must be a sequence")
    bound: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(records):
        try:
            validate_canonical_reality_gap_record_v1(item)
        except Exception as exc:
            raise AdvancedSearchValidationError(
                f"reality_gap_records[{index}] is not a COMPLETE Phase 7 record"
            ) from exc
        payload = _plain_mapping(item)
        _assert_signal_identity_compatible(
            template_identity,
            payload["experiment_identity"],
            field_name=f"reality_gap_records[{index}]",
        )
        record_id = str(payload["reality_gap_record_id"])
        if record_id in seen:
            raise AdvancedSearchValidationError("duplicate reality_gap_record_id")
        seen.add(record_id)
        bound.append(payload)
    bound.sort(key=lambda item: str(item["reality_gap_record_id"]))
    return bound


def _assert_signal_identity_compatible(
    template_identity: Mapping[str, Any], signal_identity: Mapping[str, Any], *, field_name: str
) -> None:
    comparable_fields = tuple(
        field for field in FROZEN_IDENTITY_FIELDS if field not in {"seed", "environment_digest"}
    )
    for field_name_key in comparable_fields:
        if template_identity.get(field_name_key) != signal_identity.get(field_name_key):
            raise AdvancedSearchValidationError(
                f"{field_name} is not comparable on frozen identity field {field_name_key}"
            )


def _canonicalize_meta_signals(
    signals: Sequence[Mapping[str, Any]], *, meta_learning_identity: str | None
) -> list[dict[str, Any]]:
    if not isinstance(signals, Sequence) or isinstance(signals, (str, bytes)):
        raise AdvancedSearchValidationError("meta_learning_signals must be a sequence")
    if not signals:
        if meta_learning_identity is not None:
            raise AdvancedSearchValidationError(
                "meta_learning_identity must be omitted when no signals are supplied"
            )
        return []
    identity = _require_sha256("meta_learning_identity", meta_learning_identity)
    bound: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(signals):
        if not isinstance(item, Mapping):
            raise AdvancedSearchValidationError(f"meta_learning_signals[{index}] must be a mapping")
        payload = _plain_mapping(item)
        kind = payload.get("kind")
        if kind not in CANONICAL_PROPOSAL_KINDS:
            raise AdvancedSearchValidationError("meta-learning signal kind is not canonical")
        if payload.get("authority") != META_LEARNING_AUTHORITY:
            raise AdvancedSearchValidationError(
                "meta-learning signal authority must be RESEARCH_ONLY"
            )
        if payload.get("promotion_authority") != META_PROMOTION_AUTHORITY:
            raise AdvancedSearchValidationError("meta-learning signal cannot promote")
        if payload.get("applies_to_champion") is not False:
            raise AdvancedSearchValidationError("meta-learning signal cannot apply to champion")
        proposal_id = _require_sha256(
            f"meta_learning_signals[{index}].proposal_id", payload.get("proposal_id")
        )
        if proposal_id in seen:
            raise AdvancedSearchValidationError("duplicate meta-learning proposal_id")
        seen.add(proposal_id)
        bound.append(
            {
                "applies_to_champion": False,
                "authority": META_LEARNING_AUTHORITY,
                "kind": kind,
                "meta_learning_identity": identity,
                "promotion_authority": META_PROMOTION_AUTHORITY,
                "proposal_id": proposal_id,
                "question_id": _require_token(
                    f"meta_learning_signals[{index}].question_id", payload.get("question_id")
                ),
                "reason": _require_token(
                    f"meta_learning_signals[{index}].reason", payload.get("reason")
                ),
                "target": _require_token(
                    f"meta_learning_signals[{index}].target", payload.get("target")
                ),
                "target_kind": _require_token(
                    f"meta_learning_signals[{index}].target_kind", payload.get("target_kind")
                ),
            }
        )
    bound.sort(key=lambda item: str(item["proposal_id"]))
    return bound


def _failure_signals(
    failure_records: Sequence[Mapping[str, Any]],
    *,
    gap_records: Sequence[Mapping[str, Any]],
    parameter_region: Mapping[str, Any],
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    region_matches = [
        item for item in failure_records if item.get("parameter_region") == parameter_region
    ]
    failure_classes = sorted({str(item.get("failure_class")) for item in region_matches})
    robustness_failures = [item for item in failure_classes if item in ROBUSTNESS_FAILURE_CLASSES]
    reality_gap_failures = [item for item in failure_classes if item == "REJECTED_REALITY_GAP"]
    gap_hits = [
        item
        for item in gap_records
        if item.get("overall_disposition") == DISPOSITION_REJECTED_REALITY_GAP
        and item.get("experiment_identity", {}).get("strategy_params_digest")
        == identity.get("strategy_params_digest")
    ]
    known_failure = bool(region_matches or gap_hits)
    reasons: list[str] = []
    if region_matches:
        reasons.append("known rejected parameter region")
    if robustness_failures:
        reasons.append("known robustness failure")
    if reality_gap_failures or gap_hits:
        reasons.append("known reality-gap failure")
    if failure_classes:
        reasons.append("known failure class")
    return {
        "failure_classes": failure_classes,
        "known_failure": known_failure,
        "known_failure_class": bool(failure_classes),
        "known_reality_gap_failure": bool(reality_gap_failures or gap_hits),
        "known_rejected_parameter_region": bool(region_matches),
        "known_robustness_failure": bool(robustness_failures),
        "matching_failure_record_ids": [item["failure_record_id"] for item in region_matches],
        "matching_reality_gap_record_ids": [item["reality_gap_record_id"] for item in gap_hits],
        "reason": "; ".join(reasons) if reasons else "no known failure",
    }


def _priority_from_signals(
    signals: Sequence[Mapping[str, Any]],
    *,
    strategy_family: str,
    search_space_id: str,
    hypothesis_kind: str,
    parameter_region: Mapping[str, Any],
    duplicate_assessment: Mapping[str, Any],
) -> tuple[list[str], int]:
    score = PRIORITY_NEUTRAL
    matched: list[str] = []
    for signal in signals:
        if not _signal_applies(
            signal,
            strategy_family=strategy_family,
            search_space_id=search_space_id,
            hypothesis_kind=hypothesis_kind,
            parameter_region=parameter_region,
        ):
            continue
        matched.append(str(signal["proposal_id"]))
        kind = signal["kind"]
        if kind == PROPOSAL_PRIORITIZE_RESEARCH:
            score += PRIORITY_PRIORITIZE
        elif kind == PROPOSAL_INVESTIGATE:
            score += PRIORITY_INVESTIGATE
        elif kind == PROPOSAL_DEPRIORITIZE_RESEARCH:
            score += PRIORITY_DEPRIORITIZE
        elif kind == PROPOSAL_RETEST:
            score += PRIORITY_INVESTIGATE
    if duplicate_assessment.get("detected") is True:
        score += PRIORITY_DUPLICATE_WARN
    return matched, score


def _signal_applies(
    signal: Mapping[str, Any],
    *,
    strategy_family: str,
    search_space_id: str,
    hypothesis_kind: str,
    parameter_region: Mapping[str, Any],
) -> bool:
    target = str(signal["target"])
    target_kind = str(signal["target_kind"])
    if target_kind == "strategy_family":
        return target == strategy_family
    if target_kind == "search_space_id":
        return target == search_space_id
    if target_kind == "hypothesis_kind":
        return target == hypothesis_kind
    if target_kind == "parameter_region":
        return target in {str(value) for value in parameter_region.values()} or target in {
            f"{key}={value}" for key, value in parameter_region.items()
        }
    return target in {strategy_family, search_space_id, hypothesis_kind}


def _offline_request(
    *,
    hypothesis_id: str,
    experiment_id: str,
    identity_digest: str,
    parameter_region: Mapping[str, Any],
    regime: str,
) -> dict[str, Any]:
    return {
        "executed": False,
        "experiment_id": experiment_id,
        "identity_digest": identity_digest,
        "loop_started": False,
        "parameter_region": dict(parameter_region),
        "regime": regime,
        "request_kind": OFFLINE_REQUEST_KIND,
        "schema_version": OFFLINE_LOOP_SCHEMA_VERSION,
        "selected_hypothesis_id": hypothesis_id,
    }


def _candidate_hypothesis_id(parent_hypothesis_id: str, parameter_region: Mapping[str, Any]) -> str:
    region_digest = compute_content_sha256(
        {
            "digest_algorithm": DIGEST_ALGORITHM,
            "digest_domain": f"{ADVANCED_SEARCH_DOMAIN}.parameter_region",
            "payload": dict(parameter_region),
            "schema_version": SCHEMA_VERSION,
        }
    )
    candidate = f"{parent_hypothesis_id}.{region_digest[:12]}"
    return _require_token("hypothesis_id", candidate)


def _candidate_body(
    *,
    hypothesis_id: str,
    parameter_region: Mapping[str, Any],
    status: str,
    reason: str,
    search_space_id: str,
    hypothesis_kind: str,
    strategy_family: str,
    identity: Mapping[str, Any] | None = None,
    experiment_id: str | None = None,
    fingerprint: str | None = None,
    duplicate_assessment: Mapping[str, Any] | None = None,
    failure_signals: Mapping[str, Any] | None = None,
    priority_score: int = PRIORITY_NEUTRAL,
    matched_signals: Sequence[str] = (),
    offline_experiment_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_ref = compute_content_sha256(
        {
            "digest_algorithm": DIGEST_ALGORITHM,
            "digest_domain": f"{ADVANCED_SEARCH_DOMAIN}.candidate_ref",
            "payload": {
                "hypothesis_id": hypothesis_id,
                "parameter_region": dict(parameter_region),
            },
            "schema_version": SCHEMA_VERSION,
        }
    )
    return {
        "candidate_ref": candidate_ref,
        "duplicate_assessment": dict(
            duplicate_assessment or {"actions": ["NONE"], "detected": False}
        ),
        "experiment_id": experiment_id,
        "experiment_identity": identity,
        "failure_signals": dict(failure_signals or {"known_failure": False}),
        "hypothesis_fingerprint": fingerprint,
        "hypothesis_id": hypothesis_id,
        "hypothesis_kind": hypothesis_kind,
        "matched_meta_learning_proposal_ids": list(matched_signals),
        "offline_experiment_request": (
            dict(offline_experiment_request) if offline_experiment_request is not None else None
        ),
        "parameter_region": dict(parameter_region),
        "reason": reason,
        "search_priority_score": int(priority_score),
        "search_score_is_not_canonical_ranking": True,
        "search_space_id": search_space_id,
        "status": status,
        "strategy_family": strategy_family,
    }


def _rejected_candidate(
    *,
    hypothesis_id: str,
    parameter_region: Mapping[str, Any],
    status: str,
    reason: str,
    search_space_id: str,
    hypothesis_kind: str,
    strategy_family: str,
) -> dict[str, Any]:
    return _candidate_body(
        hypothesis_id=hypothesis_id,
        parameter_region=parameter_region,
        status=status,
        reason=reason,
        search_space_id=search_space_id,
        hypothesis_kind=hypothesis_kind,
        strategy_family=strategy_family,
    )


def _hypothesis_projection(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "experiment_id": candidate["experiment_id"],
        "hypothesis_fingerprint": candidate["hypothesis_fingerprint"],
        "hypothesis_id": candidate["hypothesis_id"],
        "hypothesis_kind": candidate["hypothesis_kind"],
        "identity_digest": candidate["experiment_identity"]["identity_digest"],
        "parameter_region": candidate["parameter_region"],
        "status": candidate["status"],
    }


def _parent_lineage_ref(identity: Mapping[str, Any]) -> str | None:
    parent_lineage = identity.get("parent_lineage")
    if isinstance(parent_lineage, Mapping):
        ref = parent_lineage.get("parent_lineage_ref")
        if isinstance(ref, str):
            return ref
    return None


def _count_status(candidates: Sequence[Mapping[str, Any]], status: str) -> int:
    return sum(1 for item in candidates if item.get("status") == status)


def _require_search_method(value: Any) -> str:
    method = _require_token("search_method", value)
    if method in UNSUPPORTED_SEARCH_METHODS:
        raise AdvancedSearchValidationError(
            f"search_method is unsupported in this contract: {method}"
        )
    if method not in SUPPORTED_SEARCH_METHODS:
        raise AdvancedSearchValidationError(f"unknown search_method: {method}")
    return method


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or _CREATED_AT_RE.fullmatch(value) is None:
        raise AdvancedSearchValidationError("created_at must be a canonical UTC timestamp")
    return value


def _require_token(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdvancedSearchValidationError(f"{field_name} must be a non-empty string")
    token = value.strip()
    if token.lower() in _UNAVAILABLE_TOKENS:
        raise AdvancedSearchValidationError(f"{field_name} cannot use implicit unavailable tokens")
    if _TOKEN_RE.fullmatch(token) is None:
        raise AdvancedSearchValidationError(f"{field_name} is not a canonical token")
    return token


def _require_enum(field_name: str, value: Any, allowed: Sequence[str]) -> str:
    token = _require_token(field_name, value)
    if token not in allowed:
        raise AdvancedSearchValidationError(f"{field_name} must be one of {list(allowed)}")
    return token


def _require_positive_int(field_name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise AdvancedSearchValidationError(f"{field_name} must be a positive int")
    return value


def _require_seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AdvancedSearchValidationError("seed must be an explicit int")
    return value


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise AdvancedSearchValidationError(f"{field_name} must be 64-char lowercase sha256 hex")
    return value


def _optional_retest_reason(value: Any) -> str | None:
    if value is None:
        return None
    return _require_token("retest_reason", value)


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
    "ADVANCED_SEARCH_AUTHORITY",
    "ADVANCED_SEARCH_PRESENT",
    "AUTONOMOUS_PROMOTION",
    "AdvancedSearchValidationError",
    "BEST_SHARPE_IS_NOT_AUTO_WINNER",
    "CanonicalAdvancedSearchRequestV1",
    "PHASE_13_STARTED",
    "PROMOTION_AUTHORITY",
    "SEARCH_CAN_PROMOTE",
    "SEARCH_HAS_RUNTIME_AUTHORITY",
    "SEARCH_IS_AUTHORITY_MECHANISM",
    "SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH",
    "SUPPORTED_SEARCH_METHODS",
    "SearchAxisV1",
    "SearchConstraintV1",
    "SearchObjectiveV1",
    "SearchSpaceV1",
    "build_canonical_advanced_search_v1",
    "canonical_advanced_search_constraint_v1",
    "canonical_advanced_search_objective_v1",
    "canonical_record_payload_v1",
    "validate_canonical_advanced_search_v1",
]
