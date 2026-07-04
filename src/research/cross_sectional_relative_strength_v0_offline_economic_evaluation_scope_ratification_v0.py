"""Cross-sectional relative-strength v0 research scope definition and binding ratification v0.

Deterministic, fail-closed ratification of bounded research scope definition and
versioned binding contract for cross_sectional_relative_strength/v0.

Ratifies hypothesis, required bindings, admissible evaluation stages, and
fail-closed execution boundaries only. Does not execute economic evaluation,
backtest, walk-forward, Monte Carlo, stress, or parameter sensitivity.

RESEARCH_SCOPE_DEFINITION_RATIFIED=true and OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED=true
record bounded scope and binding contract only. ECONOMIC_EVALUATION_AUTHORIZED remains
false until a separate offline execution GO. ECONOMIC_EVALUATION_EXECUTED remains false.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_cross_sectional_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH as VERSIONED_BINDING_CONFIG_REL_PATH,
    HYPOTHESIS_ID,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    compute_implementation_digest_v0,
    materialize_versioned_research_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification.v0"
)
RATIFICATION_ID = (
    "cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0"
)
RATIFICATION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "research_scope_ratification_canonical_json_v1"
SCOPE_CLASSIFICATION = "BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0"

OPERATOR_GO_TOKEN = (
    "GO_NEW_RESEARCH_SCOPE_CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"
)
OPERATOR_SCOPE_RATIFICATION_REF = "bounded_cs_relative_strength_scope_binding_ratification_v0"
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0.json"
)

RESEARCH_SCOPE_DEFINITION_RATIFIED = True
OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = True
ECONOMIC_EVALUATION_SCOPE_RATIFIED = True
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS = False
RUNTIME_REWIRE_ADMISSIBLE = False
ALLOWED_AFTER_THIS_RATIFICATION = False
NO_EVALUATION_UNTIL_SCOPE_RATIFIED = True
NO_NEW_CANDIDATE_HOLD_EXCEPTION = True
NO_NEW_CANDIDATE_HOLD_GLOBAL_STATUS = "ACTIVE"

EVALUATION_AUTHORIZATION_STATUS = "NOT_AUTHORIZED_PENDING_SEPARATE_OFFLINE_EXECUTION_GO"
ECONOMIC_VALIDITY_STATUS = "NOT_EVALUATED"

FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION: tuple[str, ...] = (
    "strategy_id",
    "strategy_version",
    "hypothesis_id",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
)

TERMINAL_FAILED_BINDING_EXCLUSIONS: tuple[str, ...] = (
    "macd/v1",
    "macd/v2",
    "macd/v3",
    "breakout_donchian/v1",
    "ma_crossover/v1",
    "rsi_reversion/step30a",
    "composite_breakout_confirmation_vol_gated_donchian_v1",
    "trend_following/v1",
    "bollinger_bands/v1",
    "momentum_1h/v1",
    "cross_sectional_funding_rate_carry/v0",
)

ALLOWED_EVALUATION_STAGES: tuple[str, ...] = (
    "OFFLINE_BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
    "PARAMETER_SENSITIVITY",
    "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
)

PROHIBITED_ACTIONS: tuple[str, ...] = (
    "ECONOMIC_EVALUATION_EXECUTION",
    "BACKTEST_EXECUTION",
    "WALK_FORWARD_EXECUTION",
    "MONTE_CARLO_EXECUTION",
    "STRESS_EXECUTION",
    "PARAMETER_SENSITIVITY_EXECUTION",
    "RUNTIME_REWIRE",
    "RUNTIME",
    "SCHEDULER",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "CANARY",
    "LIVE",
    "ADAPTER_SUBMISSION",
    "NETWORK_ORDER_PATH",
    "ORDERS",
    "CANCELS",
    "CREDENTIALS",
    "ARMING",
    "CANDIDATE_PROMOTION",
    "POLICY_THRESHOLD_RETROFIT",
    "DATASET_SUBSTITUTION",
    "PERIOD_BINDING_SUBSTITUTION",
    "PARAMETER_SEARCH",
    "IMPLICIT_ZERO_COST",
    "FAILED_BINDING_RETRY",
    "TERMINAL_FAILED_BINDING_UNCHANGED_RETRY",
)


class ValidationVerdictEnum(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class RatificationValidationResultV0:
    verdict: ValidationVerdictEnum
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_ratification_canonical_v0(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _required_bindings_matrix_v0(
    envelope: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    binding = envelope["binding"]
    status = binding["binding_status"]
    digests = binding["digest_bindings"]
    return {
        "strategy_id": {"status": "BOUND", "value": STRATEGY_ID},
        "strategy_version": {"status": "BOUND", "value": STRATEGY_VERSION},
        "hypothesis_id": {"status": "BOUND", "value": HYPOTHESIS_ID},
        "parameter_binding": {
            "status": status["numeric_bindings_status"],
            "ref": "binding.numeric_bindings",
        },
        "dataset_binding": {
            "status": status["dataset_binding_status"],
            "ref": "binding.external_bindings.panel_ohlcv_dataset_manifest_ref",
        },
        "period_binding": {
            "status": status["period_binding_status"],
            "ref": "binding.external_bindings.evaluation_period_binding",
        },
        "instrument_binding": {
            "status": status["universe_binding_status"],
            "ref": "binding.external_bindings.pit_universe_manifest_ref",
        },
        "fee_model_binding": {
            "status": status["cost_model_binding_status"],
            "ref": "binding.external_bindings.fee_model_version",
        },
        "slippage_model_binding": {
            "status": status["cost_model_binding_status"],
            "ref": "binding.external_bindings.slippage_model_version",
        },
        "funding_model_binding": {
            "status": status["cost_model_binding_status"],
            "ref": "binding.external_bindings.funding_model_version",
        },
        "execution_model_binding": {
            "status": status["cost_model_binding_status"],
            "ref": "binding.external_bindings.execution_model_version",
        },
        "economic_policy_binding": {
            "status": "BOUND",
            "ref": "envelope.economic_policy_binding",
        },
        "implementation_digest": {
            "status": digests["implementation_digest"]["status"],
            "value": digests["implementation_digest"]["value"],
        },
        "config_digest": {
            "status": digests["config_digest"]["status"],
            "value": digests["config_digest"]["value"],
        },
        "data_digest": {
            "status": digests["data_digest"]["status"],
            "value": digests["data_digest"]["value"],
        },
    }


def _all_required_bindings_ratified_v0(matrix: Mapping[str, Mapping[str, str]]) -> bool:
    return all(entry.get("status") in {"BOUND", "COMPLETE"} for entry in matrix.values())


def materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
    *,
    repo_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _ = repo_root
    envelope = dict(versioned_binding or materialize_versioned_research_binding_v0())
    binding = envelope["binding"]
    validation = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    if not validation.valid or validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        raise ValueError("versioned_binding_not_accepted_complete")

    required_bindings_matrix = _required_bindings_matrix_v0(envelope)
    all_required_bindings_ratified = _all_required_bindings_ratified_v0(required_bindings_matrix)

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "operator_go_token": OPERATOR_GO_TOKEN,
        "operator_scope_ratification_ref": OPERATOR_SCOPE_RATIFICATION_REF,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_id": HYPOTHESIS_ID,
        "candidate_binding_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "binding_digest": envelope["binding_digest"],
        "config_digest": envelope["config_digest"],
        "data_contract_digest": envelope["data_contract_digest"],
        "implementation_digest": compute_implementation_digest_v0(),
        "parameter_binding": envelope["parameter_binding"],
        "panel_dataset_binding": envelope["panel_dataset_binding"],
        "period_binding": envelope["period_binding"],
        "instrument_binding": envelope["instrument_binding"],
        "cost_execution_binding": envelope["cost_execution_binding"],
        "economic_policy_binding": envelope["economic_policy_binding"],
        "fee_model_binding": envelope["cost_execution_binding"]["fee_model_binding"],
        "slippage_model_binding": envelope["cost_execution_binding"]["slippage_model_binding"],
        "funding_model_binding": envelope["cost_execution_binding"]["funding_model_binding"],
        "execution_model_binding": envelope["cost_execution_binding"]["execution_model_binding"],
        "walk_forward_policy_binding": envelope["economic_policy_binding"][
            "walk_forward_policy_binding"
        ],
        "monte_carlo_policy_binding": envelope["economic_policy_binding"][
            "monte_carlo_policy_binding"
        ],
        "stress_policy_binding": envelope["economic_policy_binding"]["stress_policy_binding"],
        "parameter_sensitivity_policy_binding": envelope["economic_policy_binding"][
            "parameter_sensitivity_policy_binding"
        ],
        "required_bindings_before_any_evaluation": list(REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION),
        "required_bindings_matrix": required_bindings_matrix,
        "all_required_bindings_ratified": all_required_bindings_ratified,
        "terminal_failed_binding_exclusions": list(TERMINAL_FAILED_BINDING_EXCLUSIONS),
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "allowed_evaluation_stages": list(ALLOWED_EVALUATION_STAGES),
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "research_scope_definition_ratified": RESEARCH_SCOPE_DEFINITION_RATIFIED,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_scope_ratified": ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_validity_offline_gate_pass": ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "allowed_after_this_ratification": ALLOWED_AFTER_THIS_RATIFICATION,
        "no_evaluation_until_scope_ratified": NO_EVALUATION_UNTIL_SCOPE_RATIFIED,
        "no_new_candidate_hold_exception": NO_NEW_CANDIDATE_HOLD_EXCEPTION,
        "no_new_candidate_hold_global_status": NO_NEW_CANDIDATE_HOLD_GLOBAL_STATUS,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "evaluation_authorization_status": EVALUATION_AUTHORIZATION_STATUS,
        "economic_validity_status": ECONOMIC_VALIDITY_STATUS,
        "reason_codes": [],
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
    }
    semantic_payload = {
        "strategy_id": body["strategy_id"],
        "strategy_version": body["strategy_version"],
        "hypothesis_id": body["hypothesis_id"],
        "binding_digest": body["binding_digest"],
        "scope_classification": body["scope_classification"],
        "all_required_bindings_ratified": body["all_required_bindings_ratified"],
        "offline_economic_evaluation_scope_ratified": body[
            "offline_economic_evaluation_scope_ratified"
        ],
        "economic_evaluation_authorized": body["economic_evaluation_authorized"],
    }
    body["semantic_digest"] = _stable_digest(semantic_payload)
    body["config_digest"] = envelope["config_digest"]
    body["ratification_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k not in {"ratification_digest", "semantic_digest"}}
    )
    return body


def validate_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
    ratification: Mapping[str, Any],
    *,
    expected_binding: Mapping[str, Any] | None = None,
) -> RatificationValidationResultV0:
    reasons: list[str] = []
    if ratification.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if ratification.get("research_scope_definition_ratified") is not True:
        reasons.append("SCOPE_DEFINITION_NOT_RATIFIED")
    if ratification.get("offline_economic_evaluation_scope_ratified") is not True:
        reasons.append("SCOPE_NOT_RATIFIED")
    if ratification.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append("EVALUATION_ALREADY_EXECUTED")
    if ratification.get("no_evaluation_until_scope_ratified") is not True:
        reasons.append("NO_EVALUATION_UNTIL_SCOPE_RATIFIED_VIOLATION")
    if ratification.get("all_required_bindings_ratified") is not True:
        reasons.append("REQUIRED_BINDINGS_INCOMPLETE")
    if ratification.get("authority_effect") != "NONE":
        reasons.append("AUTHORITY_EFFECT_NOT_NONE")
    if ratification.get("runtime_effect") != "NONE":
        reasons.append("RUNTIME_EFFECT_NOT_NONE")
    if ratification.get("order_effect") != "NONE":
        reasons.append("ORDER_EFFECT_NOT_NONE")
    if ratification.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if ratification.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")
    if ratification.get("economic_validity_offline_gate_pass") is not False:
        reasons.append("ECONOMIC_VALIDITY_GATE_MUST_REMAIN_FALSE")
    if ratification.get("runtime_rewire_admissible") is not False:
        reasons.append("RUNTIME_REWIRE_MUST_REMAIN_FALSE")

    if expected_binding is not None:
        if ratification.get("binding_digest") != expected_binding.get("binding_digest"):
            reasons.append("BINDING_DIGEST_MISMATCH")

    verdict = ValidationVerdictEnum.ACCEPTED if not reasons else ValidationVerdictEnum.REJECTED
    return RatificationValidationResultV0(verdict=verdict, fail_reasons=tuple(reasons))
