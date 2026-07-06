"""Cross-sectional funding-rate rank-delta v0 offline economic evaluation scope ratification v0.

Deterministic, fail-closed ratification of bounded offline-only economic evaluation
scope for cross_sectional_funding_rate_rank_delta/v0. Does not execute evaluation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_funding_rate_rank_delta_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_rate_rank_delta_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_funding_rate_rank_delta_v0_versioned_research_binding_v0 import (
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
    "CROSS_SECTIONAL_FUNDING_RATE_RANK_DELTA_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "SCOPE_RATIFICATION_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_funding_rate_rank_delta_v0_offline_economic_evaluation_scope_ratification.v0"
)
RATIFICATION_ID = (
    "cross_sectional_funding_rate_rank_delta_v0_offline_economic_evaluation_scope_ratification_v0"
)
RATIFICATION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "research_scope_ratification_canonical_json_v1"
SCOPE_CLASSIFICATION = "BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0"
RECOMMENDED_SCOPE_ID = (
    "CROSS_SECTIONAL_FUNDING_RATE_RANK_DELTA_V0_OFFLINE_ECONOMIC_EVALUATION_RATIFICATION_PREP"
)
OPERATOR_GO_RATIFICATION_PREP = (
    "GO_CROSS_SECTIONAL_FUNDING_RATE_RANK_DELTA_V0_BINDING_RATIFICATION_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
OPERATOR_SCOPE_RATIFICATION_REF = (
    "bounded_cs_funding_rate_rank_delta_v0_scope_binding_ratification_v0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_funding_rate_rank_delta_v0_offline_economic_evaluation_scope_ratification_v0.json"
)
FUTURE_RUNNER_BINDING_REF = (
    "scripts/ops/"
    "run_cross_sectional_funding_rate_rank_delta_v0_offline_economic_evaluation_execution_v0.py"
)
FUTURE_HARNESS_BINDING_REF = (
    "src/research/"
    "cross_sectional_funding_rate_rank_delta_v0_offline_economic_evaluation_execution_v0.py"
)
PARENT_TERMINAL_SCOPE_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "dual_leg_spread_v1_terminal_negative_evidence_and_next_material_scope_20260706T145350Z"
)
PARENT_DUAL_LEG_SPREAD_V1_EVALUATION_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "dual_leg_spread_v1_offline_economic_reevaluation_after_pr4929_calmar_fix_20260706T144942Z"
)

OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = True
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
EVALUATION_INFRASTRUCTURE_READY = False
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False

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
    "ORDERS",
    "CANCELS",
    "CREDENTIALS",
    "ARMING",
    "CANDIDATE_PROMOTION",
    "POLICY_THRESHOLD_RETROFIT",
    "PARAMETER_SEARCH",
    "IMPLICIT_ZERO_COST",
    "FAILED_BINDING_RETRY",
    "TERMINAL_FAILED_BINDING_UNCHANGED_RETRY",
    "PARAMETER_RESCUE",
    "THRESHOLD_RELAXATION",
)

TERMINAL_FAILED_BINDING_EXCLUSIONS: tuple[str, ...] = (
    "cross_sectional_funding_rate_dual_leg_spread/v1",
    "cross_sectional_funding_rate_delta_momentum/v0",
    "cross_sectional_funding_rate_carry/v0",
    "cross_sectional_relative_strength/v0",
    "trend_following/v2",
    "bollinger_bands/v2",
    "momentum_1h/v2",
    "trend_following/v1",
    "bollinger_bands/v1",
    "momentum_1h/v1",
    "okx_full_panel_cross_sectional_ranking/v0",
)

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
    "material_difference_digest",
)

PROMOTION_ADMISSIBLE = False
RUNTIME_REWIRE_ADMISSIBLE = False
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS = False
MATERIAL_DIFFERENCE_VS_DUAL_LEG_SPREAD_V1_CONFIRMED = True
MATERIAL_DIFFERENCE_VS_DELTA_MOMENTUM_V0_CONFIRMED = True
UNCHANGED_RETRY = False
PARAMETER_RESCUE = False
THRESHOLD_RELAXATION = False


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
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str) + "\n"


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
            "ref": "binding.external_bindings.panel_funding_dataset_manifest_ref",
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
        "material_difference_digest": {
            "status": digests["material_difference_digest"]["status"],
            "value": digests["material_difference_digest"]["value"],
        },
    }


def _all_required_bindings_ratified_v0(matrix: Mapping[str, Mapping[str, str]]) -> bool:
    return all(entry.get("status") in {"BOUND", "COMPLETE"} for entry in matrix.values())


def materialize_rank_delta_offline_economic_evaluation_scope_ratification_v0(
    *,
    repo_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _ = repo_root
    envelope = dict(versioned_binding or materialize_versioned_research_binding_v0())
    binding = envelope["binding"]
    validation = validate_funding_rate_rank_delta_ranking_semantics_binding_v0(binding)
    if not validation.valid or validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        raise ValueError("versioned_binding_not_accepted_complete")

    required_bindings_matrix = _required_bindings_matrix_v0(envelope)
    all_required_bindings_ratified = _all_required_bindings_ratified_v0(required_bindings_matrix)

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "recommended_scope_id": RECOMMENDED_SCOPE_ID,
        "operator_go_token": OPERATOR_GO_RATIFICATION_PREP,
        "operator_scope_ratification_ref": OPERATOR_SCOPE_RATIFICATION_REF,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "go_token": OPERATOR_GO_RATIFICATION_PREP,
        "scope_id": RECOMMENDED_SCOPE_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "hypothesis_class": HYPOTHESIS_ID,
        "candidate_id": f"{STRATEGY_ID}/{STRATEGY_VERSION}",
        "candidate_binding_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "binding_digest": envelope["binding_digest"],
        "config_digest": envelope["config_digest"],
        "data_digest": envelope["data_digest"],
        "material_difference_digest": envelope["material_difference_digest"],
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
        "future_runner_binding": FUTURE_RUNNER_BINDING_REF,
        "future_harness_binding": FUTURE_HARNESS_BINDING_REF,
        "evaluation_infrastructure_ready": EVALUATION_INFRASTRUCTURE_READY,
        "material_difference_basis": (
            "cross_sectional_rank_migration_not_level_spread_or_absolute_funding_delta"
        ),
        "material_difference_vs_dual_leg_spread_v1_confirmed": (
            MATERIAL_DIFFERENCE_VS_DUAL_LEG_SPREAD_V1_CONFIRMED
        ),
        "material_difference_vs_delta_momentum_v0_confirmed": (
            MATERIAL_DIFFERENCE_VS_DELTA_MOMENTUM_V0_CONFIRMED
        ),
        "unchanged_retry": UNCHANGED_RETRY,
        "parameter_rescue": PARAMETER_RESCUE,
        "threshold_relaxation": THRESHOLD_RELAXATION,
        "unchanged_retry_of_failed_bindings_forbidden": True,
        "futures_only_basis": "pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1",
        "reuse_first_basis": (
            "existing_cross_sectional_panel_funding_materialization_and_evaluation_wiring_patterns"
        ),
        "parent_terminal_scope_bundle": PARENT_TERMINAL_SCOPE_BUNDLE,
        "parent_dual_leg_spread_v1_evaluation_bundle": PARENT_DUAL_LEG_SPREAD_V1_EVALUATION_BUNDLE,
        "required_bindings_before_any_evaluation": list(REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION),
        "required_bindings_matrix": required_bindings_matrix,
        "all_required_bindings_ratified": all_required_bindings_ratified,
        "terminal_failed_binding_exclusions": list(TERMINAL_FAILED_BINDING_EXCLUSIONS),
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "research_scope_definition_ratified": True,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "binding_ratified": all_required_bindings_ratified,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_validity_offline_gate_pass": ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
        "promotion_admissible": PROMOTION_ADMISSIBLE,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "runtime_rewire": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "evaluation_authorization_status": "NOT_AUTHORIZED_PENDING_SEPARATE_OFFLINE_EXECUTION_GO",
        "economic_validity_status": "NOT_EVALUATED",
        "reason_codes": [],
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
    }
    body["ratification_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k != "ratification_digest"}
    )
    return body


def validate_rank_delta_offline_economic_evaluation_scope_ratification_v0(
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
    if ratification.get("all_required_bindings_ratified") is not True:
        reasons.append("REQUIRED_BINDINGS_INCOMPLETE")
    if ratification.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append("EVALUATION_ALREADY_EXECUTED")
    if ratification.get("promotion_admissible") is not False:
        reasons.append("PROMOTION_ADMISSIBLE_MUST_BE_FALSE")
    if ratification.get("runtime_rewire_admissible") is not False:
        reasons.append("RUNTIME_REWIRE_ADMISSIBLE_MUST_BE_FALSE")
    if ratification.get("authority_effect") != "NONE":
        reasons.append("AUTHORITY_EFFECT_NOT_NONE")
    if ratification.get("runtime_effect") != "NONE":
        reasons.append("RUNTIME_EFFECT_NOT_NONE")
    if ratification.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if ratification.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")
    if ratification.get("material_difference_vs_dual_leg_spread_v1_confirmed") is not True:
        reasons.append("MATERIAL_DIFFERENCE_VS_DUAL_LEG_SPREAD_V1_NOT_CONFIRMED")
    if ratification.get("material_difference_vs_delta_momentum_v0_confirmed") is not True:
        reasons.append("MATERIAL_DIFFERENCE_VS_DELTA_MOMENTUM_V0_NOT_CONFIRMED")
    if ratification.get("unchanged_retry_of_failed_bindings_forbidden") is not True:
        reasons.append("UNCHANGED_RETRY_FORBIDDEN_MUST_BE_TRUE")

    if expected_binding is not None:
        if ratification.get("binding_digest") != expected_binding.get("binding_digest"):
            reasons.append("BINDING_DIGEST_MISMATCH")
        if ratification.get("data_digest") != expected_binding.get("data_digest"):
            reasons.append("DATA_DIGEST_MISMATCH")

    verdict = ValidationVerdictEnum.ACCEPTED if not reasons else ValidationVerdictEnum.REJECTED
    return RatificationValidationResultV0(verdict=verdict, fail_reasons=tuple(reasons))
