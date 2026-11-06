"""Phase 8 Canonical Regime-Aware Evaluation v1 (research evidence only).

Per-regime research evaluation bound to Phase 1 Canonical Experiment
Identity. Research and runtime regime labels are never treated as silently
identical. Lookahead into decision-time labels is forbidden. This layer
has no runtime, order, live, funding, canary, promotion, or config-write
authority.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

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

SCHEMA_VERSION: Final[str] = "canonical_regime_aware_evaluation_v1"
REGIME_AWARE_DOMAIN: Final[str] = "peak_trade.canonical_regime_aware_evaluation.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
EVIDENCE_KIND_EXPERIMENT_RECORD: Final[str] = "EXPERIMENT_RECORD"
ARTIFACT_KIND_REPO_RELATIVE_REF: Final[str] = ARTIFACT_KIND_REPO_RELATIVE
ARTIFACT_KIND_STORE_RELATIVE_REF: Final[str] = ARTIFACT_KIND_STORE_RELATIVE
MAPPING_CONTRACT_VERSION: Final[str] = "canonical_regime_mapping_v1"
METRIC_DEFINITION_VERSION: Final[str] = "canonical_robustness_metrics_v1"
ROBUSTNESS_SUITE_VERSION: Final[str] = "canonical_robustness_suite_v1"

REGIME_AWARE_EVALUATION_PRESENT: Final[bool] = True
REGIME_MAPPING_EXPLICIT: Final[bool] = True
REGIME_LOOKAHEAD_BLOCKED: Final[bool] = True
CANONICAL_CORE_LOGIC_ATTRIBUTION_PRESENT: Final[bool] = True
BULL_BEAR_DECISION_QUALITY_EVALUABLE: Final[bool] = True
REGIME_AWARE_EVALUATION_HAS_RUNTIME_AUTHORITY: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_PROMOTE: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_PROMOTE_TO_LIVE: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_INCREASE_RISK: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_INCREASE_LEVERAGE: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_FUND: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_SUBMIT_ORDER: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_ARM: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_ENABLE: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
REGIME_AWARE_EVALUATION_CAN_AUTHORIZE_CANARY: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

MAPPING_MODE_EXPLICIT: Final[str] = "EXPLICIT_MAPPING"
MAPPING_MODE_SEPARATION: Final[str] = "DOCUMENTED_SEPARATION"
CANONICAL_MAPPING_MODES: Final[tuple[str, ...]] = (
    MAPPING_MODE_EXPLICIT,
    MAPPING_MODE_SEPARATION,
)

FAMILY_TREND_RANGE: Final[str] = "TREND_RANGE"
FAMILY_VOLATILITY: Final[str] = "VOLATILITY"
FAMILY_BULL_BEAR: Final[str] = "BULL_BEAR"
FAMILY_LIQUIDITY_STATE: Final[str] = "LIQUIDITY_STATE"
FAMILY_SPREAD_REGIME: Final[str] = "SPREAD_REGIME"
FAMILY_FUNDING_REGIME: Final[str] = "FUNDING_REGIME"
FAMILY_CRASH_STATE: Final[str] = "CRASH_STATE"
FAMILY_RISK_ON_OFF: Final[str] = "RISK_ON_OFF"
FAMILY_VOLATILITY_CLUSTERING: Final[str] = "VOLATILITY_CLUSTERING"
FAMILY_VENUE_MICROSTRUCTURE: Final[str] = "VENUE_MICROSTRUCTURE_STATE"
REQUIRED_REGIME_FAMILIES: Final[tuple[str, ...]] = (
    FAMILY_TREND_RANGE,
    FAMILY_VOLATILITY,
    FAMILY_BULL_BEAR,
    FAMILY_LIQUIDITY_STATE,
    FAMILY_SPREAD_REGIME,
    FAMILY_FUNDING_REGIME,
    FAMILY_CRASH_STATE,
    FAMILY_RISK_ON_OFF,
    FAMILY_VOLATILITY_CLUSTERING,
    FAMILY_VENUE_MICROSTRUCTURE,
)
CLOSED_FAMILY_LABELS: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        FAMILY_TREND_RANGE: frozenset({"trend", "range"}),
        FAMILY_VOLATILITY: frozenset({"high", "low"}),
        FAMILY_BULL_BEAR: frozenset({"bull", "bear"}),
        FAMILY_RISK_ON_OFF: frozenset({"risk-on", "risk-off"}),
    }
)
REGIME_METRIC_FIELDS: Final[tuple[str, ...]] = (
    "return",
    "sharpe",
    "drawdown",
    "turnover",
    "fee_drag",
    "slippage",
    "failure_rate",
)
STAGE_MARKET_CONTEXT: Final[str] = "MARKET_CONTEXT"
STAGE_BULL_BEAR: Final[str] = "BULL_BEAR_CLASSIFICATION"
STAGE_STATE_SWITCH: Final[str] = "STATE_SWITCH"
STAGE_SURVIVAL: Final[str] = "SURVIVAL"
STAGE_SUITABILITY: Final[str] = "SUITABILITY"
STAGE_DOUBLE_PLAY: Final[str] = "DOUBLE_PLAY"
STAGE_ENTRY_POSITION_EXIT: Final[str] = "ENTRY_POSITION_EXIT"
STAGE_ECONOMIC_OUTCOME: Final[str] = "ECONOMIC_OUTCOME"
REQUIRED_ATTRIBUTION_STAGES: Final[tuple[str, ...]] = (
    STAGE_MARKET_CONTEXT,
    STAGE_BULL_BEAR,
    STAGE_STATE_SWITCH,
    STAGE_SURVIVAL,
    STAGE_SUITABILITY,
    STAGE_DOUBLE_PLAY,
    STAGE_ENTRY_POSITION_EXIT,
    STAGE_ECONOMIC_OUTCOME,
)
STAGE_DIGEST_FIELDS: Final[Mapping[str, str]] = MappingProxyType(
    {
        STAGE_MARKET_CONTEXT: "market_context_contract_digest",
        STAGE_BULL_BEAR: "bull_bear_logic_digest",
        STAGE_STATE_SWITCH: "state_switch_logic_digest",
        STAGE_SURVIVAL: "survival_logic_digest",
        STAGE_SUITABILITY: "suitability_logic_digest",
        STAGE_DOUBLE_PLAY: "double_play_logic_digest",
        STAGE_ENTRY_POSITION_EXIT: "entry_position_exit_logic_digest",
    }
)
ATTRIBUTION_MISCLASSIFICATION: Final[str] = "MISCLASSIFICATION"
ATTRIBUTION_TIMING_ERROR: Final[str] = "TIMING_ERROR"
ATTRIBUTION_GATE_FILTER_ERROR: Final[str] = "GATE_FILTER_ERROR"
ATTRIBUTION_EXECUTION_COST_EFFECT: Final[str] = "EXECUTION_COST_EFFECT"
ATTRIBUTION_STRATEGY_EDGE: Final[str] = "STRATEGY_EDGE"
ATTRIBUTION_NOT_ATTRIBUTABLE: Final[str] = "NOT_ATTRIBUTABLE"
CANONICAL_ATTRIBUTION_CLASSES: Final[tuple[str, ...]] = (
    ATTRIBUTION_MISCLASSIFICATION,
    ATTRIBUTION_TIMING_ERROR,
    ATTRIBUTION_GATE_FILTER_ERROR,
    ATTRIBUTION_EXECUTION_COST_EFFECT,
    ATTRIBUTION_STRATEGY_EDGE,
    ATTRIBUTION_NOT_ATTRIBUTABLE,
)
QUALITY_CORRECT: Final[str] = "CORRECT"
QUALITY_INCORRECT: Final[str] = "INCORRECT"
QUALITY_TOO_EARLY: Final[str] = "TOO_EARLY"
QUALITY_TOO_LATE: Final[str] = "TOO_LATE"
CANONICAL_BULL_BEAR_QUALITY: Final[tuple[str, ...]] = (
    QUALITY_CORRECT,
    QUALITY_INCORRECT,
    QUALITY_TOO_EARLY,
    QUALITY_TOO_LATE,
)
CANONICAL_BULL_BEAR_CLASSES: Final[frozenset[str]] = frozenset({"bull", "bear"})

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
_CORE_LOGIC_DIGEST_FIELDS: Final[tuple[str, ...]] = (
    "trading_decision_core_digest",
    "market_context_contract_digest",
    "bull_bear_logic_digest",
    "state_switch_logic_digest",
    "survival_logic_digest",
    "suitability_logic_digest",
    "double_play_logic_digest",
    "entry_position_exit_logic_digest",
)
_EVIDENCE_KINDS: Final[tuple[str, ...]] = (
    EVIDENCE_KIND_EXPERIMENT_RECORD,
    ARTIFACT_KIND_REPO_RELATIVE_REF,
    ARTIFACT_KIND_STORE_RELATIVE_REF,
)

_LOGGER = logging.getLogger(__name__)


class RegimeAwareEvaluationError(ValueError):
    """Fail-closed Canonical Regime-Aware Evaluation v1 validation error."""


@dataclass(frozen=True)
class RegimeMappingRuleV1:
    research_label: str
    runtime_label: str


@dataclass(frozen=True)
class RegimeMappingContractV1:
    mapping_mode: str
    research_regime_taxonomy: str
    runtime_regime_taxonomy: str
    mapping_contract_version: str = MAPPING_CONTRACT_VERSION
    mappings: Sequence[RegimeMappingRuleV1] = ()
    documented_separation_reason: str | None = None


@dataclass(frozen=True)
class RegimeSliceV1:
    family: str
    label: str
    decision_as_of: str
    label_as_of: str
    return_value: float
    sharpe: float
    drawdown: float
    turnover: float
    fee_drag: float
    slippage: float
    failure_rate: float
    sample_size: int


@dataclass(frozen=True)
class CoreLogicAttributionV1:
    stage: str
    attribution_class: str
    sample_size: int
    decision_as_of: str
    label_as_of: str


@dataclass(frozen=True)
class BullBearDecisionQualityV1:
    predicted_class: str
    realized_class: str
    quality: str
    sample_size: int
    decision_as_of: str
    label_as_of: str
    evaluation_as_of: str


@dataclass(frozen=True)
class CanonicalRegimeAwareEvaluationRequestV1:
    experiment_identity: Mapping[str, Any]
    mapping_contract: RegimeMappingContractV1
    regime_slices: Sequence[RegimeSliceV1]
    core_logic_attribution: Sequence[CoreLogicAttributionV1]
    bull_bear_decision_quality: Sequence[BullBearDecisionQualityV1]
    evidence_refs: Sequence[Mapping[str, Any]]
    created_at: str
    metric_definitions: str = METRIC_DEFINITION_VERSION
    robustness_suite_version: str = ROBUSTNESS_SUITE_VERSION
    experiment_id: str | None = None


def build_canonical_regime_aware_evaluation_v1(
    request: CanonicalRegimeAwareEvaluationRequestV1,
) -> Mapping[str, Any]:
    identity = _require_identity(request.experiment_identity)
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if request.experiment_id is not None:
        provided = _require_sha256("experiment_id", request.experiment_id)
        if provided != experiment_id:
            raise RegimeAwareEvaluationError(
                "experiment_id is not bound to the Canonical Experiment Identity digest"
            )
    created_at = _require_created_at(request.created_at)
    metric_definitions = _require_token("metric_definitions", request.metric_definitions)
    if metric_definitions != METRIC_DEFINITION_VERSION:
        raise RegimeAwareEvaluationError("metric_definitions must reuse the Phase 4 token")
    robustness_suite_version = _require_token(
        "robustness_suite_version", request.robustness_suite_version
    )
    if robustness_suite_version != ROBUSTNESS_SUITE_VERSION:
        raise RegimeAwareEvaluationError("robustness_suite_version must reuse the Phase 4 token")
    mapping_contract = _canonicalize_mapping_contract(request.mapping_contract)
    regime_slices = _canonicalize_regime_slices(request.regime_slices, mapping_contract)
    core_logic_attribution = _canonicalize_attribution(request.core_logic_attribution, identity)
    bull_bear_decision_quality = _canonicalize_bull_bear_quality(request.bull_bear_decision_quality)
    evidence_refs = _canonicalize_evidence_refs(request.evidence_refs, experiment_id)
    body = {
        "bull_bear_decision_quality": bull_bear_decision_quality,
        "bull_bear_decision_quality_evaluable": BULL_BEAR_DECISION_QUALITY_EVALUABLE,
        "canonical_core_logic_attribution_present": CANONICAL_CORE_LOGIC_ATTRIBUTION_PRESENT,
        "canonical_trading_decision_core_bound": True,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "core_logic_attribution": core_logic_attribution,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "evidence_refs": evidence_refs,
        "experiment_id": experiment_id,
        "experiment_identity": identity,
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "mapping_contract": mapping_contract,
        "metric_definitions": metric_definitions,
        "promotion_authority": PROMOTION_AUTHORITY,
        "regime_aware_domain": REGIME_AWARE_DOMAIN,
        "regime_aware_evaluation_can_arm": REGIME_AWARE_EVALUATION_CAN_ARM,
        "regime_aware_evaluation_can_authorize_canary": (
            REGIME_AWARE_EVALUATION_CAN_AUTHORIZE_CANARY
        ),
        "regime_aware_evaluation_can_create_confirm_token": (
            REGIME_AWARE_EVALUATION_CAN_CREATE_CONFIRM_TOKEN
        ),
        "regime_aware_evaluation_can_enable": REGIME_AWARE_EVALUATION_CAN_ENABLE,
        "regime_aware_evaluation_can_fund": REGIME_AWARE_EVALUATION_CAN_FUND,
        "regime_aware_evaluation_can_increase_leverage": (
            REGIME_AWARE_EVALUATION_CAN_INCREASE_LEVERAGE
        ),
        "regime_aware_evaluation_can_increase_risk": REGIME_AWARE_EVALUATION_CAN_INCREASE_RISK,
        "regime_aware_evaluation_can_mutate_live_config": (
            REGIME_AWARE_EVALUATION_CAN_MUTATE_LIVE_CONFIG
        ),
        "regime_aware_evaluation_can_promote": REGIME_AWARE_EVALUATION_CAN_PROMOTE,
        "regime_aware_evaluation_can_promote_to_live": (
            REGIME_AWARE_EVALUATION_CAN_PROMOTE_TO_LIVE
        ),
        "regime_aware_evaluation_can_submit_order": REGIME_AWARE_EVALUATION_CAN_SUBMIT_ORDER,
        "regime_aware_evaluation_can_use_confirm_token": (
            REGIME_AWARE_EVALUATION_CAN_USE_CONFIRM_TOKEN
        ),
        "regime_aware_evaluation_can_write_live_config": (
            REGIME_AWARE_EVALUATION_CAN_WRITE_LIVE_CONFIG
        ),
        "regime_aware_evaluation_has_runtime_authority": (
            REGIME_AWARE_EVALUATION_HAS_RUNTIME_AUTHORITY
        ),
        "regime_aware_evaluation_present": REGIME_AWARE_EVALUATION_PRESENT,
        "regime_lookahead_blocked": REGIME_LOOKAHEAD_BLOCKED,
        "regime_mapping_explicit": REGIME_MAPPING_EXPLICIT,
        "regime_slices": regime_slices,
        "robustness_suite_version": robustness_suite_version,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "self_learning_self_authorizing_separation": (SELF_LEARNING_SELF_AUTHORIZING_SEPARATION),
    }
    evaluation_identity = derive_regime_aware_evaluation_identity_v1(body)
    record = dict(body)
    record["evaluation_identity"] = evaluation_identity
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_regime_aware_evaluation_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_regime_aware_evaluation_v1 built identity=%s slices=%s",
        evaluation_identity,
        len(regime_slices),
    )
    return frozen


def derive_regime_aware_evaluation_identity_v1(record_without_ids: Mapping[str, Any]) -> str:
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{REGIME_AWARE_DOMAIN}.evaluation_identity",
        "payload": _plain_mapping(record_without_ids),
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def validate_canonical_regime_aware_evaluation_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise RegimeAwareEvaluationError("regime-aware evaluation record must be a mapping")
    record = _plain_mapping(record)
    if record.get("schema_version") != SCHEMA_VERSION:
        raise RegimeAwareEvaluationError("schema_version mismatch")
    if record.get("regime_aware_domain") != REGIME_AWARE_DOMAIN:
        raise RegimeAwareEvaluationError("regime_aware_domain mismatch")
    if record.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise RegimeAwareEvaluationError("non-COMPLETE regime-aware records are forbidden")
    if record.get("digest_algorithm") != DIGEST_ALGORITHM:
        raise RegimeAwareEvaluationError("digest_algorithm mismatch")
    if record.get("regime_aware_evaluation_present") is not True:
        raise RegimeAwareEvaluationError("regime_aware_evaluation_present must be true")
    if record.get("regime_mapping_explicit") is not True:
        raise RegimeAwareEvaluationError("regime_mapping_explicit must be true")
    if record.get("regime_lookahead_blocked") is not True:
        raise RegimeAwareEvaluationError("regime_lookahead_blocked must be true")
    if record.get("canonical_core_logic_attribution_present") is not True:
        raise RegimeAwareEvaluationError("canonical_core_logic_attribution_present must be true")
    if record.get("bull_bear_decision_quality_evaluable") is not True:
        raise RegimeAwareEvaluationError("bull_bear_decision_quality_evaluable must be true")
    if record.get("regime_aware_evaluation_has_runtime_authority") is not False:
        raise RegimeAwareEvaluationError(
            "regime_aware_evaluation_has_runtime_authority must be false"
        )
    if record.get("regime_aware_evaluation_can_mutate_live_config") is not False:
        raise RegimeAwareEvaluationError(
            "regime_aware_evaluation_can_mutate_live_config must be false"
        )
    if record.get("regime_aware_evaluation_can_write_live_config") is not False:
        raise RegimeAwareEvaluationError(
            "regime_aware_evaluation_can_write_live_config must be false"
        )
    if record.get("regime_aware_evaluation_can_promote") is not False:
        raise RegimeAwareEvaluationError("regime_aware_evaluation_can_promote must be false")
    if record.get("regime_aware_evaluation_can_promote_to_live") is not False:
        raise RegimeAwareEvaluationError(
            "regime_aware_evaluation_can_promote_to_live must be false"
        )
    if record.get("regime_aware_evaluation_can_increase_risk") is not False:
        raise RegimeAwareEvaluationError("regime_aware_evaluation_can_increase_risk must be false")
    if record.get("regime_aware_evaluation_can_increase_leverage") is not False:
        raise RegimeAwareEvaluationError(
            "regime_aware_evaluation_can_increase_leverage must be false"
        )
    if record.get("regime_aware_evaluation_can_fund") is not False:
        raise RegimeAwareEvaluationError("regime_aware_evaluation_can_fund must be false")
    if record.get("regime_aware_evaluation_can_submit_order") is not False:
        raise RegimeAwareEvaluationError("regime_aware_evaluation_can_submit_order must be false")
    if record.get("regime_aware_evaluation_can_arm") is not False:
        raise RegimeAwareEvaluationError("regime_aware_evaluation_can_arm must be false")
    if record.get("regime_aware_evaluation_can_enable") is not False:
        raise RegimeAwareEvaluationError("regime_aware_evaluation_can_enable must be false")
    if record.get("regime_aware_evaluation_can_create_confirm_token") is not False:
        raise RegimeAwareEvaluationError(
            "regime_aware_evaluation_can_create_confirm_token must be false"
        )
    if record.get("regime_aware_evaluation_can_use_confirm_token") is not False:
        raise RegimeAwareEvaluationError(
            "regime_aware_evaluation_can_use_confirm_token must be false"
        )
    if record.get("regime_aware_evaluation_can_authorize_canary") is not False:
        raise RegimeAwareEvaluationError(
            "regime_aware_evaluation_can_authorize_canary must be false"
        )
    if record.get("learning_may_autonomously_replace_core_logic") is not False:
        raise RegimeAwareEvaluationError(
            "learning_may_autonomously_replace_core_logic must be false"
        )
    if record.get("self_learning_self_authorizing_separation") is not True:
        raise RegimeAwareEvaluationError("self_learning_self_authorizing_separation must be true")
    if record.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise RegimeAwareEvaluationError("promotion_authority must be NONE")
    if record.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise RegimeAwareEvaluationError("runtime_authority_impact must be NONE")
    if record.get("canonical_trading_decision_core_bound") is not True:
        raise RegimeAwareEvaluationError("canonical_trading_decision_core_bound must be true")
    identity = _require_identity(record.get("experiment_identity"))
    experiment_id = _require_sha256("experiment_id", record.get("experiment_id"))
    expected_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if experiment_id != expected_id:
        raise RegimeAwareEvaluationError(
            "experiment_id is not bound to the Canonical Experiment Identity digest"
        )
    _require_created_at(record.get("created_at"))
    metric_definitions = _require_token("metric_definitions", record.get("metric_definitions"))
    if metric_definitions != METRIC_DEFINITION_VERSION:
        raise RegimeAwareEvaluationError("metric_definitions must reuse the Phase 4 token")
    robustness_suite_version = _require_token(
        "robustness_suite_version", record.get("robustness_suite_version")
    )
    if robustness_suite_version != ROBUSTNESS_SUITE_VERSION:
        raise RegimeAwareEvaluationError("robustness_suite_version must reuse the Phase 4 token")
    for field_name in _CORE_LOGIC_DIGEST_FIELDS:
        _require_sha256(field_name, identity.get(field_name))
    mapping_contract = record.get("mapping_contract")
    if not isinstance(mapping_contract, Mapping):
        raise RegimeAwareEvaluationError("mapping_contract must be a mapping")
    _canonicalize_mapping_contract(
        RegimeMappingContractV1(
            mapping_mode=str(mapping_contract.get("mapping_mode", "")),
            mapping_contract_version=str(mapping_contract.get("mapping_contract_version", "")),
            research_regime_taxonomy=str(mapping_contract.get("research_regime_taxonomy", "")),
            runtime_regime_taxonomy=str(mapping_contract.get("runtime_regime_taxonomy", "")),
            mappings=tuple(
                RegimeMappingRuleV1(
                    research_label=str(item.get("research_label", "")),
                    runtime_label=str(item.get("runtime_label", "")),
                )
                for item in mapping_contract.get("mappings", ())
            ),
            documented_separation_reason=mapping_contract.get("documented_separation_reason"),
        )
    )
    _require_record_regime_slices(record.get("regime_slices"), mapping_contract)
    _require_record_attribution(record.get("core_logic_attribution"), identity)
    _require_record_bull_bear_quality(record.get("bull_bear_decision_quality"))
    _canonicalize_evidence_refs(record.get("evidence_refs"), experiment_id)
    evaluation_identity = _require_sha256("evaluation_identity", record.get("evaluation_identity"))
    identity_payload = {
        key: value
        for key, value in record.items()
        if key not in {"evaluation_identity", "integrity"}
    }
    expected_identity = derive_regime_aware_evaluation_identity_v1(identity_payload)
    if evaluation_identity != expected_identity:
        raise RegimeAwareEvaluationError("evaluation_identity does not match canonical content")
    integrity = record.get("integrity")
    expected_integrity = compute_content_sha256(
        {key: value for key, value in record.items() if key != "integrity"}
    )
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise RegimeAwareEvaluationError("integrity.content_sha256 mismatch")


def canonical_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def _canonicalize_mapping_contract(contract: RegimeMappingContractV1) -> dict[str, Any]:
    mode = _require_token("mapping_mode", contract.mapping_mode)
    if mode not in CANONICAL_MAPPING_MODES:
        raise RegimeAwareEvaluationError("mapping_mode is unknown or unsupported")
    version = _require_token("mapping_contract_version", contract.mapping_contract_version)
    if version != MAPPING_CONTRACT_VERSION:
        raise RegimeAwareEvaluationError("mapping_contract_version mismatch")
    research_taxonomy = _require_token(
        "research_regime_taxonomy", contract.research_regime_taxonomy
    )
    runtime_taxonomy = _require_token("runtime_regime_taxonomy", contract.runtime_regime_taxonomy)
    if research_taxonomy == runtime_taxonomy and mode != MAPPING_MODE_EXPLICIT:
        raise RegimeAwareEvaluationError(
            "research and runtime regime taxonomies cannot be treated as silently identical"
        )
    mappings = _canonicalize_mapping_rules(contract.mappings)
    if mode == MAPPING_MODE_EXPLICIT:
        if not mappings:
            raise RegimeAwareEvaluationError("EXPLICIT_MAPPING requires pairwise mapping rules")
        if contract.documented_separation_reason is not None:
            raise RegimeAwareEvaluationError(
                "EXPLICIT_MAPPING cannot carry a documented_separation_reason"
            )
        return {
            "documented_separation_reason": None,
            "mapping_contract_version": version,
            "mapping_mode": mode,
            "mappings": mappings,
            "research_regime_taxonomy": research_taxonomy,
            "runtime_regime_taxonomy": runtime_taxonomy,
        }
    if mappings:
        raise RegimeAwareEvaluationError("DOCUMENTED_SEPARATION cannot carry identity mappings")
    reason = _require_token("documented_separation_reason", contract.documented_separation_reason)
    return {
        "documented_separation_reason": reason,
        "mapping_contract_version": version,
        "mapping_mode": mode,
        "mappings": [],
        "research_regime_taxonomy": research_taxonomy,
        "runtime_regime_taxonomy": runtime_taxonomy,
    }


def _canonicalize_mapping_rules(rules: Sequence[RegimeMappingRuleV1]) -> list[dict[str, str]]:
    canonical: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        research_label = _require_token(f"mappings[{index}].research_label", rule.research_label)
        runtime_label = _require_token(f"mappings[{index}].runtime_label", rule.runtime_label)
        if research_label in seen:
            raise RegimeAwareEvaluationError(
                f"duplicate research_label in mapping contract: {research_label}"
            )
        seen.add(research_label)
        canonical.append({"research_label": research_label, "runtime_label": runtime_label})
    canonical.sort(key=lambda item: item["research_label"])
    return canonical


def _canonicalize_regime_slices(
    slices: Sequence[RegimeSliceV1],
    mapping_contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(slices, Sequence) or isinstance(slices, (str, bytes)):
        raise RegimeAwareEvaluationError("regime_slices must be a sequence")
    if not slices:
        raise RegimeAwareEvaluationError(
            "at least one regime slice per required family is required"
        )
    canonical: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    families: set[str] = set()
    research_labels: set[str] = set()
    for index, item in enumerate(slices):
        family = _require_family(item.family)
        label = _require_family_label(family, item.label)
        key = (family, label)
        if key in seen:
            raise RegimeAwareEvaluationError(f"duplicate regime slice {family}:{label}")
        seen.add(key)
        families.add(family)
        research_labels.add(label)
        decision_as_of = _require_created_at(item.decision_as_of)
        label_as_of = _require_created_at(item.label_as_of)
        _reject_lookahead(label_as_of, decision_as_of, f"regime_slices[{index}]")
        metrics = {
            "return": _require_finite_number(f"regime_slices[{index}].return", item.return_value),
            "sharpe": _require_finite_number(f"regime_slices[{index}].sharpe", item.sharpe),
            "drawdown": _require_finite_number(f"regime_slices[{index}].drawdown", item.drawdown),
            "turnover": _require_finite_number(f"regime_slices[{index}].turnover", item.turnover),
            "fee_drag": _require_finite_number(f"regime_slices[{index}].fee_drag", item.fee_drag),
            "slippage": _require_finite_number(f"regime_slices[{index}].slippage", item.slippage),
            "failure_rate": _require_failure_rate(
                f"regime_slices[{index}].failure_rate", item.failure_rate
            ),
            "sample_size": _require_positive_int(
                f"regime_slices[{index}].sample_size", item.sample_size
            ),
        }
        canonical.append(
            {
                "decision_as_of": decision_as_of,
                "family": family,
                "label": label,
                "label_as_of": label_as_of,
                "research_regime": label,
                **metrics,
            }
        )
    missing = [family for family in REQUIRED_REGIME_FAMILIES if family not in families]
    if missing:
        raise RegimeAwareEvaluationError(f"required regime families missing: {', '.join(missing)}")
    _require_mapping_coverage(mapping_contract, research_labels)
    canonical.sort(key=lambda item: (item["family"], item["label"]))
    return canonical


def _canonicalize_attribution(
    items: Sequence[CoreLogicAttributionV1],
    identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise RegimeAwareEvaluationError("core_logic_attribution must be a sequence")
    by_stage: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        stage = _require_token(f"core_logic_attribution[{index}].stage", item.stage)
        if stage not in REQUIRED_ATTRIBUTION_STAGES:
            raise RegimeAwareEvaluationError(f"unknown attribution stage: {stage}")
        if stage in by_stage:
            raise RegimeAwareEvaluationError(f"duplicate attribution stage: {stage}")
        attribution_class = _require_token(
            f"core_logic_attribution[{index}].attribution_class", item.attribution_class
        )
        if attribution_class not in CANONICAL_ATTRIBUTION_CLASSES:
            raise RegimeAwareEvaluationError(f"unknown attribution class: {attribution_class}")
        decision_as_of = _require_created_at(item.decision_as_of)
        label_as_of = _require_created_at(item.label_as_of)
        _reject_lookahead(label_as_of, decision_as_of, f"core_logic_attribution[{index}]")
        payload: dict[str, Any] = {
            "attribution_class": attribution_class,
            "decision_as_of": decision_as_of,
            "label_as_of": label_as_of,
            "sample_size": _require_positive_int(
                f"core_logic_attribution[{index}].sample_size", item.sample_size
            ),
            "stage": stage,
        }
        digest_field = STAGE_DIGEST_FIELDS.get(stage)
        if digest_field is not None:
            payload["identity_digest_field"] = digest_field
            payload["identity_digest"] = _require_sha256(digest_field, identity.get(digest_field))
        by_stage[stage] = payload
    missing = [stage for stage in REQUIRED_ATTRIBUTION_STAGES if stage not in by_stage]
    if missing:
        raise RegimeAwareEvaluationError(
            f"required attribution stages missing: {', '.join(missing)}"
        )
    return [by_stage[stage] for stage in REQUIRED_ATTRIBUTION_STAGES]


def _canonicalize_bull_bear_quality(
    items: Sequence[BullBearDecisionQualityV1],
) -> list[dict[str, Any]]:
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise RegimeAwareEvaluationError("bull_bear_decision_quality must be a sequence")
    if not items:
        raise RegimeAwareEvaluationError("bull_bear_decision_quality observations are required")
    canonical: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        predicted = _require_token(
            f"bull_bear_decision_quality[{index}].predicted_class", item.predicted_class
        )
        realized = _require_token(
            f"bull_bear_decision_quality[{index}].realized_class", item.realized_class
        )
        if predicted not in CANONICAL_BULL_BEAR_CLASSES:
            raise RegimeAwareEvaluationError("predicted_class must be bull or bear")
        if realized not in CANONICAL_BULL_BEAR_CLASSES:
            raise RegimeAwareEvaluationError("realized_class must be bull or bear")
        quality = _require_token(f"bull_bear_decision_quality[{index}].quality", item.quality)
        if quality not in CANONICAL_BULL_BEAR_QUALITY:
            raise RegimeAwareEvaluationError("bull/bear quality is unknown or unsupported")
        decision_as_of = _require_created_at(item.decision_as_of)
        label_as_of = _require_created_at(item.label_as_of)
        evaluation_as_of = _require_created_at(item.evaluation_as_of)
        _reject_lookahead(label_as_of, decision_as_of, f"bull_bear_decision_quality[{index}]")
        if _parse_utc(evaluation_as_of) < _parse_utc(decision_as_of):
            raise RegimeAwareEvaluationError(
                "bull_bear_decision_quality evaluation_as_of cannot precede decision_as_of"
            )
        canonical.append(
            {
                "decision_as_of": decision_as_of,
                "evaluation_as_of": evaluation_as_of,
                "label_as_of": label_as_of,
                "predicted_class": predicted,
                "quality": quality,
                "realized_class": realized,
                "sample_size": _require_positive_int(
                    f"bull_bear_decision_quality[{index}].sample_size", item.sample_size
                ),
            }
        )
    canonical.sort(
        key=lambda item: (item["predicted_class"], item["quality"], item["decision_as_of"])
    )
    return canonical


def _require_record_regime_slices(value: Any, mapping_contract: Mapping[str, Any]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RegimeAwareEvaluationError("regime_slices must be a sequence")
    reconstructed: list[RegimeSliceV1] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise RegimeAwareEvaluationError(f"regime_slices[{index}] must be a mapping")
        reconstructed.append(
            RegimeSliceV1(
                family=str(item.get("family", "")),
                label=str(item.get("label", "")),
                decision_as_of=str(item.get("decision_as_of", "")),
                label_as_of=str(item.get("label_as_of", "")),
                return_value=item.get("return"),  # type: ignore[arg-type]
                sharpe=item.get("sharpe"),  # type: ignore[arg-type]
                drawdown=item.get("drawdown"),  # type: ignore[arg-type]
                turnover=item.get("turnover"),  # type: ignore[arg-type]
                fee_drag=item.get("fee_drag"),  # type: ignore[arg-type]
                slippage=item.get("slippage"),  # type: ignore[arg-type]
                failure_rate=item.get("failure_rate"),  # type: ignore[arg-type]
                sample_size=item.get("sample_size"),  # type: ignore[arg-type]
            )
        )
        if item.get("research_regime") != item.get("label"):
            raise RegimeAwareEvaluationError(
                f"regime_slices[{index}].research_regime must equal label"
            )
        extra = set(str(key) for key in item.keys()) - {
            "decision_as_of",
            "drawdown",
            "failure_rate",
            "family",
            "fee_drag",
            "label",
            "label_as_of",
            "research_regime",
            "return",
            "sample_size",
            "sharpe",
            "slippage",
            "turnover",
        }
        if extra:
            raise RegimeAwareEvaluationError(
                f"regime_slices[{index}] contains unsupported keys: {sorted(extra)}"
            )
    _canonicalize_regime_slices(reconstructed, mapping_contract)


def _require_record_attribution(value: Any, identity: Mapping[str, Any]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RegimeAwareEvaluationError("core_logic_attribution must be a sequence")
    reconstructed: list[CoreLogicAttributionV1] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise RegimeAwareEvaluationError(f"core_logic_attribution[{index}] must be a mapping")
        reconstructed.append(
            CoreLogicAttributionV1(
                stage=str(item.get("stage", "")),
                attribution_class=str(item.get("attribution_class", "")),
                sample_size=item.get("sample_size"),  # type: ignore[arg-type]
                decision_as_of=str(item.get("decision_as_of", "")),
                label_as_of=str(item.get("label_as_of", "")),
            )
        )
    expected = _canonicalize_attribution(reconstructed, identity)
    if _plain_mapping(value) != expected:
        raise RegimeAwareEvaluationError("core_logic_attribution canonical content mismatch")


def _require_record_bull_bear_quality(value: Any) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RegimeAwareEvaluationError("bull_bear_decision_quality must be a sequence")
    reconstructed: list[BullBearDecisionQualityV1] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise RegimeAwareEvaluationError(
                f"bull_bear_decision_quality[{index}] must be a mapping"
            )
        reconstructed.append(
            BullBearDecisionQualityV1(
                predicted_class=str(item.get("predicted_class", "")),
                realized_class=str(item.get("realized_class", "")),
                quality=str(item.get("quality", "")),
                sample_size=item.get("sample_size"),  # type: ignore[arg-type]
                decision_as_of=str(item.get("decision_as_of", "")),
                label_as_of=str(item.get("label_as_of", "")),
                evaluation_as_of=str(item.get("evaluation_as_of", "")),
            )
        )
    expected = _canonicalize_bull_bear_quality(reconstructed)
    if _plain_mapping(value) != expected:
        raise RegimeAwareEvaluationError("bull_bear_decision_quality canonical content mismatch")


def _require_mapping_coverage(
    mapping_contract: Mapping[str, Any],
    research_labels: set[str],
) -> None:
    mode = mapping_contract["mapping_mode"]
    if mode != MAPPING_MODE_EXPLICIT:
        return
    covered = {item["research_label"] for item in mapping_contract["mappings"]}
    missing = sorted(research_labels - covered)
    if missing:
        raise RegimeAwareEvaluationError(
            f"EXPLICIT_MAPPING missing research labels: {', '.join(missing)}"
        )


def _require_family(value: Any) -> str:
    token = _require_token("regime family", value)
    if token not in REQUIRED_REGIME_FAMILIES:
        raise RegimeAwareEvaluationError(f"regime family is unknown or unsupported: {token}")
    return token


def _require_family_label(family: str, value: Any) -> str:
    token = _require_token("regime label", value)
    allowed = CLOSED_FAMILY_LABELS.get(family)
    if allowed is not None and token not in allowed:
        raise RegimeAwareEvaluationError(f"regime label {token} is not valid for family {family}")
    return token


def _require_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RegimeAwareEvaluationError("experiment_identity present and valid is required")
    identity = _plain_mapping(value)
    try:
        validate_canonical_experiment_identity_v1(identity)
    except CanonicalExperimentIdentityError as exc:
        raise RegimeAwareEvaluationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    return identity


def _canonicalize_evidence_refs(value: Any, experiment_id: str) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise RegimeAwareEvaluationError("evidence_refs must be a sequence")
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    experiment_bound = False
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise RegimeAwareEvaluationError(f"evidence_refs[{index}] must be a mapping")
        kind = item.get("kind")
        if kind not in _EVIDENCE_KINDS:
            raise RegimeAwareEvaluationError(f"evidence_refs[{index}].kind is unsupported")
        digest = _require_sha256(f"evidence_refs[{index}].digest", item.get("digest"))
        if kind == EVIDENCE_KIND_EXPERIMENT_RECORD:
            ref = _require_sha256(f"evidence_refs[{index}].ref", item.get("ref"))
            if ref == experiment_id:
                experiment_bound = True
        else:
            ref = _require_relative_artifact_ref(f"evidence_refs[{index}].ref", item.get("ref"))
        extra_keys = set(str(key) for key in item.keys()) - {"kind", "ref", "digest"}
        if extra_keys:
            raise RegimeAwareEvaluationError(
                f"evidence_refs[{index}] contains unsupported keys: {sorted(extra_keys)}"
            )
        key = (str(kind), ref)
        if key in seen:
            raise RegimeAwareEvaluationError("duplicate evidence_refs are forbidden")
        seen.add(key)
        refs.append({"digest": digest, "kind": str(kind), "ref": ref})
    if not experiment_bound:
        raise RegimeAwareEvaluationError("evidence_refs must include the bound EXPERIMENT_RECORD")
    refs.sort(key=lambda item: (item["kind"], item["ref"]))
    return refs


def _require_relative_artifact_ref(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or value.startswith("/"):
        raise RegimeAwareEvaluationError(f"{field_name} must be a relative POSIX path")
    if ".." in value.split("/"):
        raise RegimeAwareEvaluationError(
            f"{field_name} path traversal or empty segments are forbidden"
        )
    if "\\" in value:
        raise RegimeAwareEvaluationError(f"{field_name} must use store-/repo-relative POSIX paths")
    return value


def _reject_lookahead(label_as_of: str, decision_as_of: str, field_name: str) -> None:
    if _parse_utc(label_as_of) > _parse_utc(decision_as_of):
        raise RegimeAwareEvaluationError(
            f"{field_name} lookahead is forbidden: label_as_of exceeds decision_as_of"
        )


def _parse_utc(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise RegimeAwareEvaluationError("timestamps must be timezone-aware UTC")
    return parsed.astimezone(timezone.utc)


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise RegimeAwareEvaluationError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise RegimeAwareEvaluationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


def _require_token(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not _TOKEN_RE.fullmatch(value):
        raise RegimeAwareEvaluationError(f"{field_name} is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise RegimeAwareEvaluationError(f"{field_name} cannot use implicit unavailable tokens")
    return value


def _require_finite_number(field_name: str, value: Any) -> float:
    if value is None:
        raise RegimeAwareEvaluationError(
            f"{field_name} is missing; silent zero defaults are forbidden"
        )
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RegimeAwareEvaluationError(f"{field_name} must be an explicit finite number")
    number = float(value)
    if not math.isfinite(number):
        raise RegimeAwareEvaluationError(f"non-finite numeric values are forbidden in {field_name}")
    return number


def _require_failure_rate(field_name: str, value: Any) -> float:
    number = _require_finite_number(field_name, value)
    if number < 0.0 or number > 1.0:
        raise RegimeAwareEvaluationError(f"{field_name} must be in [0, 1]")
    return number


def _require_positive_int(field_name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RegimeAwareEvaluationError(f"{field_name} must be a positive int")
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
    "BULL_BEAR_DECISION_QUALITY_EVALUABLE",
    "BullBearDecisionQualityV1",
    "CANONICAL_CORE_LOGIC_ATTRIBUTION_PRESENT",
    "CanonicalRegimeAwareEvaluationRequestV1",
    "CoreLogicAttributionV1",
    "MAPPING_MODE_EXPLICIT",
    "MAPPING_MODE_SEPARATION",
    "PROMOTION_AUTHORITY",
    "REGIME_AWARE_EVALUATION_CAN_MUTATE_LIVE_CONFIG",
    "REGIME_AWARE_EVALUATION_CAN_PROMOTE",
    "REGIME_AWARE_EVALUATION_HAS_RUNTIME_AUTHORITY",
    "REGIME_AWARE_EVALUATION_PRESENT",
    "REGIME_LOOKAHEAD_BLOCKED",
    "REGIME_MAPPING_EXPLICIT",
    "REQUIRED_REGIME_FAMILIES",
    "RegimeAwareEvaluationError",
    "RegimeMappingContractV1",
    "RegimeMappingRuleV1",
    "RegimeSliceV1",
    "SCHEMA_VERSION",
    "build_canonical_regime_aware_evaluation_v1",
    "canonical_record_payload",
    "validate_canonical_regime_aware_evaluation_v1",
]
