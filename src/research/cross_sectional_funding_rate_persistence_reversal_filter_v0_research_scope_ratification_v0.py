"""Cross-sectional funding-rate persistence reversal filter v0 research scope ratification v0.

Deterministic, fail-closed ratification of bounded offline-only research scope definition
for cross_sectional_funding_rate_persistence_reversal_filter/v0. Does not execute evaluation,
does not ratify versioned bindings, and does not touch runtime authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_"
    "RESEARCH_SCOPE_RATIFICATION_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_funding_rate_persistence_reversal_filter_v0_research_scope_ratification.v0"
)
RATIFICATION_ID = (
    "cross_sectional_funding_rate_persistence_reversal_filter_v0_research_scope_ratification_v0"
)
RATIFICATION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "research_scope_ratification_canonical_json_v1"
SCOPE_CLASSIFICATION = "BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_RATIFICATION_V0_NO_EVAL"
RECOMMENDED_SCOPE_ID = (
    "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_RESEARCH_SCOPE_RATIFICATION"
)
OPERATOR_GO_SCOPE_RATIFICATION = (
    "GO_RATIFY_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_"
    "SCOPE_ONLY_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
OPERATOR_SCOPE_RATIFICATION_REF = (
    "bounded_cs_funding_rate_persistence_reversal_filter_v0_research_scope_ratification_v0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_funding_rate_persistence_reversal_filter_v0_research_scope_ratification_v0.json"
)

STRATEGY_ID = "cross_sectional_funding_rate_persistence_reversal_filter"
STRATEGY_VERSION = "v0"
HYPOTHESIS_ID = "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_NON_BITCOIN_PERPETUALS_V0"

PARENT_TERMINAL_SCOPE_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "rank_delta_v0_terminal_negative_evidence_and_next_scope_boundary_20260706T154311Z"
)
PARENT_RANK_DELTA_V0_EVALUATION_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "rank_delta_v0_offline_economic_evaluation_20260706T153949Z"
)
TERMINALIZED_PARENT_STRATEGY = "cross_sectional_funding_rate_rank_delta/v0"

RESEARCH_SCOPE_DEFINITION_RATIFIED = True
BINDING_RATIFIED = False
ALL_REQUIRED_BINDINGS_RATIFIED = False
OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = False
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO = True
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False

PROMOTION_GRANTED = False
PROMOTION_ADMISSIBLE = False
RUNTIME_AUTHORITY_TOUCHED = False
RUNTIME_REWIRE_ADMISSIBLE = False
AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

UNCHANGED_RETRY_ALLOWED = False
PARAMETER_RESCUE = False
THRESHOLD_RELAXATION = False
CORE_SYSTEM_MUTATION_ALLOWED = False
CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED = False
MASTER_V2_MUTATION_ALLOWED = False
DOUBLE_PLAY_MUTATION_ALLOWED = False
RISK_SIZING_MUTATION_ALLOWED = False
SAFETY_RUNTIME_MUTATION_ALLOWED = False

NO_ORDERS = True
NO_CREDENTIALS = True
NO_SCHEDULER = True
NO_SHADOW = True
NO_PAPER = True
NO_TESTNET = True
NO_LIVE = True

MATERIAL_DIFFERENCE_VS_RANK_DELTA_V0_CONFIRMED = True
MATERIAL_DIFFERENCE_VS_DUAL_LEG_SPREAD_V1_CONFIRMED = True
MATERIAL_DIFFERENCE_VS_DELTA_MOMENTUM_V0_CONFIRMED = True
MATERIAL_DIFFERENCE_VS_CARRY_V0_CONFIRMED = True

PROHIBITED_ACTIONS: tuple[str, ...] = (
    "ECONOMIC_EVALUATION_EXECUTION",
    "BACKTEST_EXECUTION",
    "WALK_FORWARD_EXECUTION",
    "MONTE_CARLO_EXECUTION",
    "STRESS_EXECUTION",
    "PARAMETER_SENSITIVITY_EXECUTION",
    "PARAMETER_SEARCH",
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
    "PROMOTION",
    "POLICY_THRESHOLD_RETROFIT",
    "IMPLICIT_ZERO_COST",
    "FAILED_BINDING_RETRY",
    "TERMINAL_FAILED_BINDING_UNCHANGED_RETRY",
    "UNCHANGED_RANK_DELTA_V0_BINDING_RETRY",
    "PARAMETER_RESCUE",
    "THRESHOLD_RELAXATION",
    "VERSIONED_BINDING_RATIFICATION_IN_THIS_SCOPE",
    "CORE_SYSTEM_MUTATION",
    "CANONICAL_TRADING_LOGIC_MUTATION",
    "MASTER_V2_MUTATION",
    "DOUBLE_PLAY_MUTATION",
    "RISK_SIZING_MUTATION",
    "SAFETY_RUNTIME_MUTATION",
)

TERMINAL_FAILED_BINDING_EXCLUSIONS: tuple[str, ...] = (
    "cross_sectional_funding_rate_rank_delta/v0",
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


def _material_difference_digest_v0() -> str:
    return _stable_digest(
        {
            "primary_signal_axis": "funding_persistence_duration_decay_stability_reversal_risk_gate",
            "entry_gate": "multi_epoch_persistence_plus_adverse_reversal_block",
            "crowding_model": "explicit_reversal_trap_filter",
            "terminal_parent": TERMINALIZED_PARENT_STRATEGY,
            "rank_delta_reuse_forbidden": True,
        }
    )


def materialize_persistence_reversal_filter_research_scope_ratification_v0(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    _ = repo_root
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "recommended_scope_id": RECOMMENDED_SCOPE_ID,
        "operator_go_token": OPERATOR_GO_SCOPE_RATIFICATION,
        "operator_scope_ratification_ref": OPERATOR_SCOPE_RATIFICATION_REF,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "go_token": OPERATOR_GO_SCOPE_RATIFICATION,
        "scope_id": RECOMMENDED_SCOPE_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "hypothesis_class": HYPOTHESIS_ID,
        "candidate_id": f"{STRATEGY_ID}/{STRATEGY_VERSION}",
        "material_difference_basis": (
            "funding_persistence_reversal_filter_not_rank_delta_rotation_or_level_spread"
        ),
        "material_difference_digest": _material_difference_digest_v0(),
        "material_difference_vs_rank_delta_v0_confirmed": (
            MATERIAL_DIFFERENCE_VS_RANK_DELTA_V0_CONFIRMED
        ),
        "material_difference_vs_dual_leg_spread_v1_confirmed": (
            MATERIAL_DIFFERENCE_VS_DUAL_LEG_SPREAD_V1_CONFIRMED
        ),
        "material_difference_vs_delta_momentum_v0_confirmed": (
            MATERIAL_DIFFERENCE_VS_DELTA_MOMENTUM_V0_CONFIRMED
        ),
        "material_difference_vs_carry_v0_confirmed": MATERIAL_DIFFERENCE_VS_CARRY_V0_CONFIRMED,
        "unchanged_retry": UNCHANGED_RETRY_ALLOWED,
        "unchanged_retry_allowed": UNCHANGED_RETRY_ALLOWED,
        "parameter_rescue": PARAMETER_RESCUE,
        "threshold_relaxation": THRESHOLD_RELAXATION,
        "unchanged_retry_of_failed_bindings_forbidden": True,
        "futures_only_basis": "pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1",
        "reuse_first_basis": (
            "existing_cross_sectional_panel_funding_materialization_and_evaluation_wiring_patterns"
        ),
        "parent_terminal_scope_bundle": PARENT_TERMINAL_SCOPE_BUNDLE,
        "parent_rank_delta_v0_evaluation_bundle": PARENT_RANK_DELTA_V0_EVALUATION_BUNDLE,
        "terminalized_parent_strategy": TERMINALIZED_PARENT_STRATEGY,
        "required_bindings_before_any_evaluation": list(REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION),
        "required_bindings_matrix": {
            field: {"status": "PENDING_FUTURE_BINDING_RATIFICATION", "ref": field}
            for field in REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION
        },
        "all_required_bindings_ratified": ALL_REQUIRED_BINDINGS_RATIFIED,
        "terminal_failed_binding_exclusions": list(TERMINAL_FAILED_BINDING_EXCLUSIONS),
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "research_scope_definition_ratified": RESEARCH_SCOPE_DEFINITION_RATIFIED,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "binding_ratified": BINDING_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "next_scope_requires_separate_evaluation_go": NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO,
        "promotion_granted": PROMOTION_GRANTED,
        "promotion_admissible": PROMOTION_ADMISSIBLE,
        "runtime_authority_touched": RUNTIME_AUTHORITY_TOUCHED,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "runtime_rewire": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "evaluation_authorization_status": (
            "NOT_AUTHORIZED_PENDING_SEPARATE_BINDING_AND_OFFLINE_EXECUTION_GO"
        ),
        "economic_validity_status": "NOT_EVALUATED",
        "core_system_mutation_allowed": CORE_SYSTEM_MUTATION_ALLOWED,
        "canonical_trading_logic_mutation_allowed": CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED,
        "master_v2_mutation_allowed": MASTER_V2_MUTATION_ALLOWED,
        "double_play_mutation_allowed": DOUBLE_PLAY_MUTATION_ALLOWED,
        "risk_sizing_mutation_allowed": RISK_SIZING_MUTATION_ALLOWED,
        "safety_runtime_mutation_allowed": SAFETY_RUNTIME_MUTATION_ALLOWED,
        "no_orders": NO_ORDERS,
        "no_credentials": NO_CREDENTIALS,
        "no_scheduler": NO_SCHEDULER,
        "no_shadow": NO_SHADOW,
        "no_paper": NO_PAPER,
        "no_testnet": NO_TESTNET,
        "no_live": NO_LIVE,
        "reason_codes": [],
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
    }
    body["ratification_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k != "ratification_digest"}
    )
    return body


def validate_persistence_reversal_filter_research_scope_ratification_v0(
    ratification: Mapping[str, Any],
) -> RatificationValidationResultV0:
    reasons: list[str] = []
    if ratification.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if ratification.get("research_scope_definition_ratified") is not True:
        reasons.append("SCOPE_DEFINITION_NOT_RATIFIED")
    if ratification.get("offline_economic_evaluation_scope_ratified") is not False:
        reasons.append("OFFLINE_EVALUATION_SCOPE_MUST_NOT_BE_RATIFIED_IN_SCOPE_ONLY_PASS")
    if ratification.get("binding_ratified") is not False:
        reasons.append("BINDING_RATIFIED_MUST_BE_FALSE_IN_SCOPE_ONLY_PASS")
    if ratification.get("all_required_bindings_ratified") is not False:
        reasons.append("ALL_REQUIRED_BINDINGS_MUST_NOT_BE_RATIFIED_IN_SCOPE_ONLY_PASS")
    if ratification.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append("EVALUATION_ALREADY_EXECUTED")
    if ratification.get("next_scope_requires_separate_evaluation_go") is not True:
        reasons.append("NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO_MUST_BE_TRUE")
    if ratification.get("promotion_granted") is not False:
        reasons.append("PROMOTION_GRANTED_MUST_BE_FALSE")
    if ratification.get("promotion_admissible") is not False:
        reasons.append("PROMOTION_ADMISSIBLE_MUST_BE_FALSE")
    if ratification.get("runtime_authority_touched") is not False:
        reasons.append("RUNTIME_AUTHORITY_TOUCHED_MUST_BE_FALSE")
    if ratification.get("runtime_rewire_admissible") is not False:
        reasons.append("RUNTIME_REWIRE_ADMISSIBLE_MUST_BE_FALSE")
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
    if ratification.get("material_difference_vs_rank_delta_v0_confirmed") is not True:
        reasons.append("MATERIAL_DIFFERENCE_VS_RANK_DELTA_V0_NOT_CONFIRMED")
    if ratification.get("unchanged_retry_of_failed_bindings_forbidden") is not True:
        reasons.append("UNCHANGED_RETRY_FORBIDDEN_MUST_BE_TRUE")
    if ratification.get("unchanged_retry_allowed") is not False:
        reasons.append("UNCHANGED_RETRY_ALLOWED_MUST_BE_FALSE")
    if ratification.get("core_system_mutation_allowed") is not False:
        reasons.append("CORE_SYSTEM_MUTATION_ALLOWED_MUST_BE_FALSE")
    if ratification.get("no_orders") is not True:
        reasons.append("NO_ORDERS_MUST_BE_TRUE")
    if ratification.get("no_live") is not True:
        reasons.append("NO_LIVE_MUST_BE_TRUE")
    if TERMINALIZED_PARENT_STRATEGY not in ratification.get(
        "terminal_failed_binding_exclusions", []
    ):
        reasons.append("TERMINALIZED_PARENT_STRATEGY_NOT_EXCLUDED")

    verdict = ValidationVerdictEnum.ACCEPTED if not reasons else ValidationVerdictEnum.REJECTED
    return RatificationValidationResultV0(verdict=verdict, fail_reasons=tuple(reasons))
