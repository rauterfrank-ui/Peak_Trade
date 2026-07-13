"""Cross-sectional MA-crossover panel rank-rotation v0 research scope ratification v1.

Deterministic, fail-closed ratification of bounded offline-only research scope definition
for cross_sectional_ma_crossover_panel_rank_rotation/v0. Reuses unchanged ma_crossover/v1
signal logic under a new cross-sectional panel composition archetype. Does not execute
evaluation, does not ratify versioned bindings, does not materialize datasets, and does
not touch runtime authority.
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
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_RATIFICATION_V1=true"
)

SCHEMA_VERSION = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification.v1"
)
RATIFICATION_ID = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1"
)
RATIFICATION_VERSION = "v1"
CANONICAL_SERIALIZATION_VERSION = "research_scope_ratification_canonical_json_v1"
SCOPE_CLASSIFICATION = (
    "NEW_CROSS_SECTIONAL_MULTI_INSTRUMENT_COMPOSITION_EVIDENCE_CLASS_"
    "BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_RATIFICATION_V1_NO_EVAL"
)
RECOMMENDED_SCOPE_ID = (
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_RATIFICATION"
)
OPERATOR_GO_SCOPE_RATIFICATION = (
    "GO_RATIFY_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_"
    "RESEARCH_SCOPE_NO_EVAL_NO_RUNTIME_AUTHORITY_V1"
)
OPERATOR_SCOPE_RATIFICATION_REF = (
    "bounded_cs_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1.json"
)
PANEL_BINDING_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_panel_universe_dataset_binding_v0.json"
)
MATERIAL_DIFFERENCE_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_material_difference_and_non_claim_contract_v0.json"
)
UNCHANGED_RETRY_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_unchanged_retry_and_near_duplicate_block_v0.json"
)
PHASE3_PRECONDITION_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_precondition_contract_v0.json"
)

STRATEGY_ID = "cross_sectional_ma_crossover_panel_rank_rotation"
STRATEGY_VERSION = "v0"
UNDERLYING_SIGNAL_STRATEGY_ID = "ma_crossover"
UNDERLYING_SIGNAL_STRATEGY_VERSION = "v1"
UNDERLYING_SIGNAL_BINDING = "ma_crossover/v1@inst-eth-usdt-perp"
HYPOTHESIS_ID = "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_NON_BITCOIN_PERPETUALS_V0"

SOURCE_DISCOVERY_EVIDENCE_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/"
    "cross_sectional_multi_instrument_futures_panel_scope_discovery_and_ratification_prep_v0_"
    "20260710T085834Z"
)
SOURCE_ADJUDICATION_EVIDENCE_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/"
    "cross_sectional_ma_crossover_panel_scope_discovery_contradiction_adjudication_and_"
    "corrected_ratification_prep_v0_20260710T090302Z"
)
UNDERLYING_SINGLE_INSTRUMENT_EVALUATION_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "economic_evaluation/bounded_step29m_ma_crossover_v1_post_binding_fix_economic_evaluation_"
    "recovery_single_run_v0_20260702T012057Z"
)
UNDERLYING_SINGLE_INSTRUMENT_CLOSEOUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "economic_evaluation/bounded_step29m_ma_crossover_v1_economic_policy_fail_closeout_and_"
    "candidate_decision_read_only_v0_20260702T012719Z"
)
TERMINAL_UNDERLYING_SIGNAL_BINDING = "ma_crossover/v1@inst-eth-usdt-perp"
TERMINAL_UNDERLYING_CONFIG_DIGEST = (
    "301231ab06d6fa52f09dee6812104b164c79b92dee765e50ee9247701ad45ffd"
)
TERMINAL_UNDERLYING_DATASET_DIGEST = (
    "39286384bb5baca27c93cae04716de9d8638ac62ab7d01a64c0a74c535e8d087"
)

PHASE3_GO_TOKEN_TO_REGISTER_ONLY = (
    "GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0"
)

FAST_WINDOW = 20
SLOW_WINDOW = 50
PRICE_COL = "close"

RESEARCH_SCOPE_DEFINITION_RATIFIED = True
RESEARCH_SCOPE_RATIFIED = True
BINDING_RATIFIED = False
ALL_REQUIRED_BINDINGS_RATIFIED = False
OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = False
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
DATASET_MATERIALIZED = False
NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO = True
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

SINGLE_INSTRUMENT_EVIDENCE = "TERMINAL_NEGATIVE"
PANEL_ARCHETYPE_EVIDENCE = "NOT_PREVIOUSLY_EXECUTED"
UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED = True
MATERIAL_DIFFERENCE_CONFIRMED = True
SIGNAL_FAMILY_MATERIAL_DIFFERENCE = False

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
SIGNAL_LOGIC_CHANGE_ALLOWED = False
PARAMETER_OPTIMIZATION_ALLOWED = False
POLICY_RESCUE_ALLOWED = False
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

MATERIAL_DIFFERENCE_AXES: tuple[str, ...] = (
    "PORTFOLIO_AGGREGATION=SINGLE_INSTRUMENT_DIRECT_TO_CROSS_SECTIONAL_SCORE_AND_TOP1_ROTATION",
    "UNIVERSE=ETH_ONLY_TO_LIFECYCLE_ADMISSIBLE_OKX_NON_BITCOIN_PERPETUAL_PANEL",
    "DATASET=INST_ETH_USDT_PERP_1M_TO_NEW_PIT_OKX_PT1H_LIFECYCLE_PANEL",
    "EVALUATION_GEOMETRY=DIRECT_SINGLE_SLOT_TO_MULTI_INSTRUMENT_RANK_ROTATION",
)

EXPLICIT_NON_CLAIMS: tuple[str, ...] = (
    "SIGNAL_UNTESTED=false",
    "NO_PRIOR_SINGLE_INSTRUMENT_EVALUATION=false",
    "NEW_SIGNAL_FAMILY=false",
    "TERMINAL_SINGLE_INSTRUMENT_EVIDENCE_SUPERSEDED=false",
    "DATASET_CHANGE_ALONE_SUFFICIENT=false",
)

PROHIBITED_ACTIONS: tuple[str, ...] = (
    "DATASET_MATERIALIZATION",
    "NETWORK_INGEST",
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
    "UNCHANGED_MA_CROSSOVER_V1_SINGLE_INSTRUMENT_BINDING_RETRY",
    "PARAMETER_RESCUE",
    "THRESHOLD_RELAXATION",
    "POLICY_RESCUE",
    "STRATEGY_LOGIC_CHANGE",
    "PARAMETER_CHANGE",
    "VERSIONED_BINDING_RATIFICATION_IN_THIS_SCOPE",
    "CORE_SYSTEM_MUTATION",
    "CANONICAL_TRADING_LOGIC_MUTATION",
    "MASTER_V2_MUTATION",
    "DOUBLE_PLAY_MUTATION",
    "RISK_SIZING_MUTATION",
    "SAFETY_RUNTIME_MUTATION",
)

TERMINAL_FAILED_BINDING_EXCLUSIONS: tuple[str, ...] = (
    "ma_crossover/v1@inst-eth-usdt-perp",
    "vol_breakout/v1@inst-eth-usdt-perp",
    "cross_sectional_relative_strength/v0",
    "cross_sectional_realized_volatility_rank_rotation/v0",
    "cross_sectional_funding_rate_rank_delta/v0",
    "cross_sectional_funding_rate_dual_leg_spread/v1",
    "cross_sectional_funding_rate_delta_momentum/v0",
    "cross_sectional_funding_rate_carry/v0",
    "cross_sectional_funding_rate_persistence_reversal_filter/v0",
    "cross_sectional_funding_rate_dispersion_zscore_reversion/v0",
    "okx_full_panel_cross_sectional_ranking/v0",
    "trend_following/v2",
    "bollinger_bands/v2",
    "momentum_1h/v2",
    "trend_following/v1",
    "bollinger_bands/v1",
    "momentum_1h/v1",
)

NEAR_DUPLICATE_BLOCKS: tuple[str, ...] = (
    "ma_crossover/v1_same_binding_panel_retry",
    "ma_crossover/v1_new_panel_same_single_slot_geometry",
    "okx_full_panel_relative_strength_rank_archetype_relabel_as_ma_crossover",
    "final_fleet_v1_on_new_panel_only",
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
class RatificationValidationResultV1:
    verdict: ValidationVerdictEnum
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_ratification_canonical_v1(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str) + "\n"


def _material_difference_digest_v1() -> str:
    return _stable_digest(
        {
            "material_difference_basis": (
                "TRUE_MULTI_INSTRUMENT_CROSS_SECTIONAL_SCORE_COMPOSITION_TOP1_ROTATION_"
                "AND_NEW_LIFECYCLE_PANEL"
            ),
            "material_difference_axes": list(MATERIAL_DIFFERENCE_AXES),
            "signal_family_material_difference": SIGNAL_FAMILY_MATERIAL_DIFFERENCE,
            "underlying_signal_binding": UNDERLYING_SIGNAL_BINDING,
            "panel_archetype": "cross_sectional_ma_crossover_panel_rank_rotation/v0",
        }
    )


def materialize_panel_universe_dataset_binding_v0() -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "cross_sectional_ma_crossover_panel_rank_rotation_panel_binding.v0",
        "panel_id": "pit_okx_linear_usdt_non_bitcoin_pt1h_panel",
        "universe_policy_id": (
            "pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe/v1"
        ),
        "lifecycle_policy_id": "okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1",
        "dataset_schema": "pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1",
        "bar_interval": "PT1H",
        "min_instruments": 5,
        "venue": "OKX",
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "selection_policy": "TOP1_BY_CANONICAL_MA_CROSSOVER_SCORE",
        "max_active_instruments": 1,
        "rotation_requires_reconciled_flat": True,
        "underlying_signal_strategy_id": UNDERLYING_SIGNAL_STRATEGY_ID,
        "underlying_signal_strategy_version": UNDERLYING_SIGNAL_STRATEGY_VERSION,
        "fast_window": FAST_WINDOW,
        "slow_window": SLOW_WINDOW,
        "price_col": PRICE_COL,
        "signal_logic_change_allowed": SIGNAL_LOGIC_CHANGE_ALLOWED,
        "parameter_optimization_allowed": PARAMETER_OPTIMIZATION_ALLOWED,
        "binding_status": "SCOPE_DEFINED_NOT_RATIFIED",
    }
    body["binding_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k != "binding_digest"}
    )
    return body


def materialize_material_difference_and_non_claim_contract_v0() -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": (
            "cross_sectional_ma_crossover_panel_rank_rotation_material_difference_contract.v0"
        ),
        "material_difference_basis": (
            "TRUE_MULTI_INSTRUMENT_CROSS_SECTIONAL_SCORE_COMPOSITION_TOP1_ROTATION_"
            "AND_NEW_LIFECYCLE_PANEL"
        ),
        "material_difference_confirmed": MATERIAL_DIFFERENCE_CONFIRMED,
        "material_difference_axes": list(MATERIAL_DIFFERENCE_AXES),
        "signal_family_material_difference": SIGNAL_FAMILY_MATERIAL_DIFFERENCE,
        "explicit_non_claims": list(EXPLICIT_NON_CLAIMS),
        "single_instrument_evidence": SINGLE_INSTRUMENT_EVIDENCE,
        "panel_archetype_evidence": PANEL_ARCHETYPE_EVIDENCE,
        "underlying_signal_binding": UNDERLYING_SIGNAL_BINDING,
        "material_difference_digest": _material_difference_digest_v1(),
    }
    body["contract_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k != "contract_digest"}
    )
    return body


def materialize_unchanged_retry_and_near_duplicate_block_v0() -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": (
            "cross_sectional_ma_crossover_panel_rank_rotation_unchanged_retry_block.v0"
        ),
        "unchanged_single_instrument_retry_blocked": UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED,
        "unchanged_retry_allowed": UNCHANGED_RETRY_ALLOWED,
        "terminal_underlying_signal_binding": TERMINAL_UNDERLYING_SIGNAL_BINDING,
        "terminal_underlying_config_digest": TERMINAL_UNDERLYING_CONFIG_DIGEST,
        "terminal_underlying_dataset_digest": TERMINAL_UNDERLYING_DATASET_DIGEST,
        "terminal_underlying_status": "ROBUSTNESS_FAILED",
        "terminal_failed_binding_exclusions": list(TERMINAL_FAILED_BINDING_EXCLUSIONS),
        "near_duplicate_blocks": list(NEAR_DUPLICATE_BLOCKS),
        "not_near_duplicate_confirmed": {
            "proposed_archetype": "cross_sectional_ma_crossover_panel_rank_rotation/v0",
            "reason": (
                "No existing evaluated cross-sectional scope combines ma_crossover "
                "per-instrument score with top-1 rotation on lifecycle PT1H panel; "
                "okx_full_panel terminal archetype used relative_strength price-return "
                "rank, not ma_crossover score."
            ),
        },
    }
    body["block_digest"] = _stable_digest({k: v for k, v in body.items() if k != "block_digest"})
    return body


def materialize_phase3_precondition_contract_v0() -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": (
            "cross_sectional_ma_crossover_panel_rank_rotation_phase3_precondition.v0"
        ),
        "phase3_go_token_to_register_only": PHASE3_GO_TOKEN_TO_REGISTER_ONLY,
        "dataset_materialization_authorized": False,
        "network_ingest_authorized": False,
        "economic_evaluation_authorized": False,
        "required_preconditions": [
            "RESEARCH_SCOPE_RATIFIED=true",
            "VERSIONED_BINDING_RATIFICATION_REQUIRES_SEPARATE_GO",
            "DATASET_MATERIALIZATION_REQUIRES_SEPARATE_GO",
        ],
        "reuse_first_owners": [
            "scripts/ops/materialize_okx_production_lifecycle_and_pt1h_panel_v1.py",
            "src/research/pit_okx_pt1h_panel_ohlcv_dataset_v1",
            "src/research/cross_sectional_panel_economic_evaluation_wiring_v0",
            "src/research/cross_sectional_single_slot_backtest_wiring_v0",
        ],
        "next_action_after_scope_ratification": (
            "PHASE3_DATASET_MATERIALIZATION_REQUIRES_SEPARATE_GO"
        ),
    }
    body["precondition_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k != "precondition_digest"}
    )
    return body


def materialize_ma_crossover_panel_rank_rotation_research_scope_ratification_v1(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    _ = repo_root
    panel_binding = materialize_panel_universe_dataset_binding_v0()
    material_difference = materialize_material_difference_and_non_claim_contract_v0()
    unchanged_retry = materialize_unchanged_retry_and_near_duplicate_block_v0()
    phase3 = materialize_phase3_precondition_contract_v0()

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
        "underlying_signal_strategy_id": UNDERLYING_SIGNAL_STRATEGY_ID,
        "underlying_signal_strategy_version": UNDERLYING_SIGNAL_STRATEGY_VERSION,
        "underlying_signal_binding": UNDERLYING_SIGNAL_BINDING,
        "go_token": OPERATOR_GO_SCOPE_RATIFICATION,
        "scope_id": RECOMMENDED_SCOPE_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "hypothesis_class": HYPOTHESIS_ID,
        "candidate_id": f"{STRATEGY_ID}/{STRATEGY_VERSION}",
        "material_difference_basis": material_difference["material_difference_basis"],
        "material_difference_digest": material_difference["material_difference_digest"],
        "material_difference_confirmed": MATERIAL_DIFFERENCE_CONFIRMED,
        "material_difference_axes": list(MATERIAL_DIFFERENCE_AXES),
        "signal_family_material_difference": SIGNAL_FAMILY_MATERIAL_DIFFERENCE,
        "explicit_non_claims": list(EXPLICIT_NON_CLAIMS),
        "single_instrument_evidence": SINGLE_INSTRUMENT_EVIDENCE,
        "panel_archetype_evidence": PANEL_ARCHETYPE_EVIDENCE,
        "unchanged_single_instrument_retry_blocked": UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED,
        "unchanged_retry": UNCHANGED_RETRY_ALLOWED,
        "unchanged_retry_allowed": UNCHANGED_RETRY_ALLOWED,
        "parameter_rescue": PARAMETER_RESCUE,
        "threshold_relaxation": THRESHOLD_RELAXATION,
        "policy_rescue_allowed": POLICY_RESCUE_ALLOWED,
        "signal_logic_change_allowed": SIGNAL_LOGIC_CHANGE_ALLOWED,
        "parameter_optimization_allowed": PARAMETER_OPTIMIZATION_ALLOWED,
        "unchanged_retry_of_failed_bindings_forbidden": True,
        "futures_only_basis": (
            "pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe/v1"
        ),
        "reuse_first_basis": (
            "reuse_unchanged_ma_crossover_v1_signal_with_cross_sectional_score_composition_"
            "adapter_and_new_lifecycle_pt1h_panel_binding"
        ),
        "source_discovery_evidence_bundle": SOURCE_DISCOVERY_EVIDENCE_BUNDLE,
        "source_adjudication_evidence_bundle": SOURCE_ADJUDICATION_EVIDENCE_BUNDLE,
        "underlying_single_instrument_evaluation_bundle": UNDERLYING_SINGLE_INSTRUMENT_EVALUATION_BUNDLE,
        "underlying_single_instrument_closeout_bundle": UNDERLYING_SINGLE_INSTRUMENT_CLOSEOUT_BUNDLE,
        "terminal_underlying_signal_binding": TERMINAL_UNDERLYING_SIGNAL_BINDING,
        "terminal_underlying_config_digest": TERMINAL_UNDERLYING_CONFIG_DIGEST,
        "terminal_underlying_dataset_digest": TERMINAL_UNDERLYING_DATASET_DIGEST,
        "panel_universe_dataset_binding": panel_binding,
        "material_difference_and_non_claim_contract": material_difference,
        "unchanged_retry_and_near_duplicate_block": unchanged_retry,
        "phase3_precondition_contract": phase3,
        "phase3_go_token_to_register_only": PHASE3_GO_TOKEN_TO_REGISTER_ONLY,
        "fast_window": FAST_WINDOW,
        "slow_window": SLOW_WINDOW,
        "price_col": PRICE_COL,
        "required_bindings_before_any_evaluation": list(REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION),
        "required_bindings_matrix": {
            field: {"status": "PENDING_FUTURE_BINDING_RATIFICATION", "ref": field}
            for field in REQUIRED_BINDINGS_BEFORE_ANY_EVALUATION
        },
        "all_required_bindings_ratified": ALL_REQUIRED_BINDINGS_RATIFIED,
        "terminal_failed_binding_exclusions": list(TERMINAL_FAILED_BINDING_EXCLUSIONS),
        "near_duplicate_blocks": list(NEAR_DUPLICATE_BLOCKS),
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "research_scope_definition_ratified": RESEARCH_SCOPE_DEFINITION_RATIFIED,
        "research_scope_ratified": RESEARCH_SCOPE_RATIFIED,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "binding_ratified": BINDING_RATIFIED,
        "dataset_materialized": DATASET_MATERIALIZED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "next_scope_requires_separate_evaluation_go": NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO,
        "promotion_granted": PROMOTION_GRANTED,
        "promotion_admissible": PROMOTION_ADMISSIBLE,
        "runtime_authority_touched": RUNTIME_AUTHORITY_TOUCHED,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
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


def validate_ma_crossover_panel_rank_rotation_research_scope_ratification_v1(
    ratification: Mapping[str, Any],
) -> RatificationValidationResultV1:
    reasons: list[str] = []
    if ratification.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if ratification.get("research_scope_definition_ratified") is not True:
        reasons.append("SCOPE_DEFINITION_NOT_RATIFIED")
    if ratification.get("research_scope_ratified") is not True:
        reasons.append("RESEARCH_SCOPE_NOT_RATIFIED")
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
    if ratification.get("dataset_materialized") is not False:
        reasons.append("DATASET_MATERIALIZED_MUST_BE_FALSE")
    if ratification.get("single_instrument_evidence") != SINGLE_INSTRUMENT_EVIDENCE:
        reasons.append("SINGLE_INSTRUMENT_EVIDENCE_NOT_TERMINAL_NEGATIVE")
    if ratification.get("panel_archetype_evidence") != PANEL_ARCHETYPE_EVIDENCE:
        reasons.append("PANEL_ARCHETYPE_EVIDENCE_NOT_NOT_PREVIOUSLY_EXECUTED")
    if ratification.get("unchanged_single_instrument_retry_blocked") is not True:
        reasons.append("UNCHANGED_SINGLE_INSTRUMENT_RETRY_NOT_BLOCKED")
    if ratification.get("material_difference_confirmed") is not True:
        reasons.append("MATERIAL_DIFFERENCE_NOT_CONFIRMED")
    if ratification.get("signal_family_material_difference") is not False:
        reasons.append("SIGNAL_FAMILY_MATERIAL_DIFFERENCE_MUST_BE_FALSE")
    if ratification.get("next_scope_requires_separate_evaluation_go") is not True:
        reasons.append("NEXT_SCOPE_REQUIRES_SEPARATE_EVALUATION_GO_MUST_BE_TRUE")
    if ratification.get("promotion_granted") is not False:
        reasons.append("PROMOTION_GRANTED_MUST_BE_FALSE")
    if ratification.get("runtime_authority_touched") is not False:
        reasons.append("RUNTIME_AUTHORITY_TOUCHED_MUST_BE_FALSE")
    if ratification.get("authority_effect") != "NONE":
        reasons.append("AUTHORITY_EFFECT_NOT_NONE")
    if ratification.get("runtime_effect") != "NONE":
        reasons.append("RUNTIME_EFFECT_NOT_NONE")
    if ratification.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if ratification.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")
    if ratification.get("spot_allowed") is not False:
        reasons.append("SPOT_ALLOWED_MUST_BE_FALSE")
    if ratification.get("signal_logic_change_allowed") is not False:
        reasons.append("SIGNAL_LOGIC_CHANGE_MUST_BE_FALSE")
    if ratification.get("parameter_optimization_allowed") is not False:
        reasons.append("PARAMETER_OPTIMIZATION_MUST_BE_FALSE")
    if ratification.get("unchanged_retry_of_failed_bindings_forbidden") is not True:
        reasons.append("UNCHANGED_RETRY_FORBIDDEN_MUST_BE_TRUE")
    if ratification.get("unchanged_retry_allowed") is not False:
        reasons.append("UNCHANGED_RETRY_ALLOWED_MUST_BE_FALSE")
    if TERMINAL_UNDERLYING_SIGNAL_BINDING not in ratification.get(
        "terminal_failed_binding_exclusions", []
    ):
        reasons.append("TERMINAL_UNDERLYING_BINDING_NOT_EXCLUDED")
    if ratification.get("underlying_signal_binding") != UNDERLYING_SIGNAL_BINDING:
        reasons.append("UNDERLYING_SIGNAL_BINDING_MISMATCH")
    if ratification.get("fast_window") != FAST_WINDOW:
        reasons.append("FAST_WINDOW_MISMATCH")
    if ratification.get("slow_window") != SLOW_WINDOW:
        reasons.append("SLOW_WINDOW_MISMATCH")
    if ratification.get("phase3_go_token_to_register_only") != PHASE3_GO_TOKEN_TO_REGISTER_ONLY:
        reasons.append("PHASE3_GO_TOKEN_MISMATCH")

    verdict = ValidationVerdictEnum.ACCEPTED if not reasons else ValidationVerdictEnum.REJECTED
    return RatificationValidationResultV1(verdict=verdict, fail_reasons=tuple(reasons))
