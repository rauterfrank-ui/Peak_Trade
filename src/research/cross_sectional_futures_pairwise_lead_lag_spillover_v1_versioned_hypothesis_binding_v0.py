"""Versioned hypothesis binding for cross_sectional_futures_pairwise_lead_lag_spillover/v1.

Binds the ratified pairwise directed spillover graph hypothesis on the canonical PIT OHLCV
cross-sectional panel. Research-only; no runtime, authority, or economic evaluation effect.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0 import (
    BOUND_PORTFOLIO_BINDING_STATUS,
    PORTFOLIO_BINDING_GO_TOKEN,
    PORTFOLIO_BINDING_SCOPE,
    PRE_PORTFOLIO_BINDING_DIGEST,
    build_portfolio_implementation_bindings_v0,
    validate_portfolio_implementation_bindings_v0,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    MANIFEST_ARTIFACT_ID,
    UNIVERSE_ID,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_VERSIONED_HYPOTHESIS_BINDING_V0=true"
)
BINDING_ARTIFACT_VERSION = "v0"
BINDING_SCHEMA_VERSION = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding.v0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_VERSIONED_HYPOTHESIS_BINDING_V0.md"
)
CONFIRM_GO = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_VERSIONED_HYPOTHESIS_BINDING_"
    "RATIFICATION_V0"
)
MATERIALIZATION_CONFIRM_GO = CONFIRM_GO

REQUIRED_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "preflight.txt",
    "source_manifest_verification.txt",
    "owner_inventory.json",
    "reuse_decision.json",
    "field_classification.json",
    "hypothesis_contract.json",
    "dataset_binding.json",
    "universe_binding.json",
    "period_binding.json",
    "score_family_policy.json",
    "distinctness_and_negative_evidence_protection.json",
    "digest_contracts.json",
    "digest_dependency_graph.json",
    "before_after_field_diff.json",
    "semantic_identity_comparison.json",
    "cryptographic_identity_comparison.json",
    "materializer_roundtrip.txt",
    "deterministic_materialization.txt",
    "test_assertion_matrix.json",
    "test_results.txt",
    "final_report.txt",
    "MANIFEST.sha256",
)

STRATEGY_ID = "cross_sectional_futures_pairwise_lead_lag_spillover"
STRATEGY_VERSION = "v1"
HYPOTHESIS_CLASS = "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER"
RESEARCH_HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_NON_BITCOIN_PERPETUALS_V1"
)
RESEARCH_SCOPE = "cross_sectional_futures_pairwise_lead_lag_spillover/v1"
STRATEGY_FAMILY = "pairwise_leader_follower_spillover_v1"
HYPOTHESIS_FAMILY = STRATEGY_FAMILY
SCORE_FAMILY_POLICY = "pairwise_spillover_graph_v1"
MARKET_SCOPE = "OKX_LINEAR_USDT_NON_BITCOIN_FUTURES"
BAR_INTERVAL = "PT1H"
DATASET_POLICY = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
UNIVERSE_POLICY = "pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1"
TIMESTAMP_ALIGNMENT = "common_utc_hourly_close_intersection_no_forward_fill"

PANEL_DATASET_ID = DATASET_POLICY
PANEL_DATASET_VERSION = "v1"
PANEL_DATASET_SCHEMA = "pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1"
PANEL_DATASET_MANIFEST_REF = (
    f"pit_okx_pt1h_panel_ohlcv_dataset_v1:{PANEL_DATASET_ID}:{PANEL_DATASET_VERSION}"
)
PIT_UNIVERSE_MANIFEST_REF = f"pit_futures_universe_manifest_v1:{MANIFEST_ARTIFACT_ID}"
UNIVERSE_LIFECYCLE_REGISTRY_REF = "pit_futures_lifecycle_registry_v1:okx_production_lifecycle_v1"
ADMISSIBILITY_MANIFEST_REF = (
    f"pit_cross_sectional_research_dataset_envelope.v0:{PANEL_DATASET_ID}:{PANEL_DATASET_VERSION}"
)
PERIOD_BINDING_ID = "pit_cross_sectional_research_chronological_holdout_v1"
PERIOD_BINDING_REF = f"{PERIOD_BINDING_ID}:v1"

RATIFIED_NORMALIZED_PANEL_DIGEST = (
    "79b1c977960f4af7e1eb54580738d77b259b74f7f02bbf0e999afbb95f8f09f1"
)
RATIFIED_PANEL_MANIFEST_DIGEST = "36b333ffd52e6465c5de3d0fca8267bea01ab4e476afa94412352fecbe7ac01a"
RATIFIED_LIFECYCLE_REGISTRY_DIGEST = (
    "79713e9b84a8d6e9afa54f36ef89c3e1a844d8d2b79d0cb26bec18a8f3473a92"
)

PRIOR_LEAD_LAG_SCOPE = "cross_sectional_futures_lead_lag_information_diffusion/v0"
PRIOR_LEAD_LAG_HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_NON_BITCOIN_PERPETUALS_V0"
)
PRIOR_LEAD_LAG_BINDING_DIGEST = "9e9ab5676d8859d819dad1aed1eaa78163529682492fcc333ead001841e414c1"
PRIOR_LEAD_LAG_SCORE_FAMILY = "panel_median_benchmark_lagged_return_diffusion_v0"
PRIOR_LEAD_LAG_SCOPE_STATUS = "TERMINAL_INSUFFICIENT_SAMPLE"
MATERIAL_DIFFERENCE_CLASS = "PAIRWISE_DIRECTED_GRAPH_VS_PANEL_MEDIAN_DIFFUSION"

PAIR_DEFINITION = "ordered_directed_pairs_i_to_j_with_i_not_equal_j"
LEADER_FEATURE_FAMILY = "lagged_return_and_optional_lagged_ohlcv_only"
FOLLOWER_TARGET_FAMILY = "strictly_future_return"
PAIRWISE_RELATION_OUTPUT = "directed_spillover_strength"
GRAPH_OUTPUT = "directed_weighted_pairwise_spillover_graph"
PENDING_IMPLEMENTATION_STATUS = "PENDING_SEPARATE_IMPLEMENTATION_BINDING"

ADMISSIBLE_SCORE_FAMILIES: frozenset[str] = frozenset({SCORE_FAMILY_POLICY})

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
PR5198_CLOSEOUT_BUNDLE = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5198_merge_closeout_cross_sectional_futures_lead_lag_information_diffusion_v0_"
    "terminal_insufficient_sample_and_distinct_futures_research_scope_ratification_v0_"
    "20260715T032558Z"
)
SOURCE_SCOPE_RATIFICATION_BUNDLE = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_"
    "sample_and_distinct_futures_research_scope_ratification_v0_20260715T031703Z"
)
SOURCE_PARENT_EVALUATION_BUNDLE = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0_20260715T030542Z"
)
SOURCE_FEASIBILITY_BUNDLE_NOT_YET_MATERIALIZED = True

FEE_MODEL_VERSION = "backtest_fee_taker_symmetric_v0"
FEE_BPS_PER_SIDE = 10.0
SLIPPAGE_MODEL_VERSION = "backtest_slippage_symmetric_v0"
SLIPPAGE_BPS_PER_SIDE = 5.0
FUNDING_MODEL_VERSION = "backtest_funding_perpetual_interval_v1"
SPREAD_MODEL_VERSION = "research_conservative_bps_v1"
CONSERVATIVE_HALF_SPREAD_BPS = 5.0
EXECUTION_MODEL_VERSION = "backtest_execution_v0"
EFFECTIVE_ENTRY_COST_BPS = FEE_BPS_PER_SIDE + SLIPPAGE_BPS_PER_SIDE + CONSERVATIVE_HALF_SPREAD_BPS
EFFECTIVE_EXIT_COST_BPS = EFFECTIVE_ENTRY_COST_BPS
ROUNDTRIP_COST_BPS = EFFECTIVE_ENTRY_COST_BPS + EFFECTIVE_EXIT_COST_BPS

WALK_FORWARD_POLICY_VERSION = "walk_forward_v1"
MONTE_CARLO_POLICY_VERSION = "monte_carlo_v1"
MONTE_CARLO_RUNS = 64
MONTE_CARLO_SEED = 42
STRESS_POLICY_VERSION = "stress_class_suite_v1"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

NEXT_RECOMMENDED_SCOPE = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0"
)
NEXT_OPERATOR_GO = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0"
)
PRE_RATIFIED_BINDING_DIGEST = PRE_PORTFOLIO_BINDING_DIGEST
SUPERSESSION_MODE = "PORTFOLIO_BINDING_COMPLETION_SUPERSESSION_V0"

ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"
MANIFEST_OWNER = "scripts.ops.primary_evidence_retention_v0"
MATERIALIZER_OWNER = (
    "scripts.research."
    "materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
    "versioned_hypothesis_binding_v0"
)
VALIDATOR_OWNER = (
    "src.research."
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0"
)


class BindingMaterializationVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REJECTED = "REJECTED"


class BindingValidationVerdict(str, Enum):
    ACCEPTED_COMPLETE = "ACCEPTED_COMPLETE"
    REJECTED_INCOMPLETE = "REJECTED_INCOMPLETE"


@dataclass(frozen=True)
class VersionedHypothesisBindingResultV0:
    verdict: BindingMaterializationVerdict
    validation_verdict: BindingValidationVerdict
    binding: dict[str, Any]
    fail_reasons: tuple[str, ...]


def _field_bound(*, value: Any = None, ref: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"status": "BOUND"}
    if value is not None:
        payload["value"] = value
    if ref:
        payload["ref"] = ref
    return payload


def _field_pending(*, ref: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"status": PENDING_IMPLEMENTATION_STATUS}
    if ref:
        payload["ref"] = ref
    return payload


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": (
                "cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
                "versioned_hypothesis_binding_v0"
            ),
            "portfolio_binding_module": (
                "cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0"
            ),
            "orchestrator": ORCHESTRATOR_OWNER,
            "score_family_policy": SCORE_FAMILY_POLICY,
            "hypothesis_family": HYPOTHESIS_FAMILY,
            "schema_version": BINDING_SCHEMA_VERSION,
            "portfolio_binding_scope": PORTFOLIO_BINDING_SCOPE,
        }
    )


def compute_data_contract_digest_v0() -> str:
    return _stable_digest(
        {
            "dataset_id": PANEL_DATASET_ID,
            "dataset_policy": DATASET_POLICY,
            "panel_manifest_ref": PANEL_DATASET_MANIFEST_REF,
            "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
            "normalized_panel_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
        }
    )


def compute_universe_digest_v0() -> str:
    return _stable_digest(
        {
            "universe_id": UNIVERSE_ID,
            "universe_policy_id": UNIVERSE_POLICY_ID,
            "lifecycle_registry_digest": RATIFIED_LIFECYCLE_REGISTRY_DIGEST,
            "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        }
    )


def compute_period_binding_digest_v0(period_binding: Mapping[str, Any] | None = None) -> str:
    payload = period_binding if period_binding is not None else build_period_binding_v0()
    return _stable_digest(payload)


def compute_material_difference_digest_v0() -> str:
    return _stable_digest(
        {
            "prior_scope": PRIOR_LEAD_LAG_SCOPE,
            "prior_scope_status": PRIOR_LEAD_LAG_SCOPE_STATUS,
            "prior_score_family": PRIOR_LEAD_LAG_SCORE_FAMILY,
            "new_score_family": SCORE_FAMILY_POLICY,
            "material_difference_class": MATERIAL_DIFFERENCE_CLASS,
            "distinct_hypothesis": True,
            "same_semantic_binding": False,
            "unchanged_retry": False,
            "pairwise_directed_graph": True,
            "panel_median_benchmark_forbidden": True,
        }
    )


def build_hypothesis_statement_v0() -> str:
    return (
        "Cross-sectional futures pairwise lead-lag spillover hypothesis: model admissible "
        "futures instruments as graph nodes and directed leader-to-follower edges; infer "
        "pairwise spillover strength from strictly lagged leader features to strictly future "
        "follower returns on finalized PT1H OHLCV without panel-median diffusion semantics."
    )


def build_pairwise_hypothesis_contract_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "research_scope": RESEARCH_SCOPE,
        "hypothesis_family": HYPOTHESIS_FAMILY,
        "score_family": SCORE_FAMILY_POLICY,
        "market_scope": MARKET_SCOPE,
        "bar_interval": BAR_INTERVAL,
        "dataset_policy": DATASET_POLICY,
        "universe_policy": UNIVERSE_POLICY,
        "timestamp_alignment": TIMESTAMP_ALIGNMENT,
        "finalized_bars_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "node_semantics": "single_admissible_futures_instrument",
        "edge_semantics": "directed_leader_to_follower_relation",
        "pair_definition": PAIR_DEFINITION,
        "leader_feature_family": LEADER_FEATURE_FAMILY,
        "follower_target_family": FOLLOWER_TARGET_FAMILY,
        "pairwise_relation_output": PAIRWISE_RELATION_OUTPUT,
        "graph_output": GRAPH_OUTPUT,
        "feature_time_lt_decision_time_required": True,
        "target_time_gt_decision_time_required": True,
        "contemporaneous_target_leakage_forbidden": True,
        "forward_fill_forbidden": True,
        "unfinalized_bars_forbidden": True,
        "survivorship_shortcut_forbidden": True,
        "panel_median_benchmark_semantics_forbidden": True,
        "lead_lag_v0_binding_reuse_forbidden": True,
        "lead_lag_v0_retry_forbidden": True,
        "policy_rescue_forbidden": True,
        "self_pair_i_equals_j_forbidden": True,
        "undirected_or_unordered_pair_ambiguity_forbidden": True,
    }


def build_pending_implementation_bindings_v0() -> dict[str, Any]:
    return build_portfolio_implementation_bindings_v0()


def build_material_difference_from_prior_v0() -> dict[str, Any]:
    return {
        "prior_scope": PRIOR_LEAD_LAG_SCOPE,
        "prior_scope_status": PRIOR_LEAD_LAG_SCOPE_STATUS,
        "prior_lead_lag_hypothesis_id": PRIOR_LEAD_LAG_HYPOTHESIS_ID,
        "prior_lead_lag_score_family": PRIOR_LEAD_LAG_SCORE_FAMILY,
        "prior_lead_lag_binding_digest": PRIOR_LEAD_LAG_BINDING_DIGEST,
        "material_difference_proven": True,
        "material_difference_class": MATERIAL_DIFFERENCE_CLASS,
        "same_dataset_allowed": True,
        "same_mechanism": False,
        "same_score_family": False,
        "same_binding": False,
        "unchanged_retry": False,
        "negative_evidence_preserved": True,
        "policy_rescue": False,
        "new_score_family_policy": SCORE_FAMILY_POLICY,
        "mechanism_delta": (
            "panel_median_benchmark_lagged_return_diffusion vs pairwise_directed_spillover_graph"
        ),
        "graph_structure_delta": "panel_median_scalar_diffusion vs directed_dyadic_edges",
        "prior_binding_not_reused_unchanged": True,
        "unchanged_retry_blocked": True,
        "lead_lag_v0_binding_reuse_forbidden": True,
        "parent_terminal_evaluation_bundle": str(SOURCE_PARENT_EVALUATION_BUNDLE),
    }


def build_parameter_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "pair_definition": PAIR_DEFINITION,
        "leader_feature_family": LEADER_FEATURE_FAMILY,
        "follower_target_family": FOLLOWER_TARGET_FAMILY,
        "pairwise_relation_output": PAIRWISE_RELATION_OUTPUT,
        "graph_output": GRAPH_OUTPUT,
        "parameter_search_forbidden": True,
        "lag_optimization_forbidden": True,
        "threshold_optimization_forbidden": True,
        "prior_lead_lag_binding_not_reused_unchanged": True,
        "unchanged_retry_of_failed_bindings_forbidden": True,
    }


def build_pit_universe_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "venue": "OKX",
        "instrument_type": "LINEAR_PERPETUAL",
        "settlement_asset": "USDT",
        "market_scope": MARKET_SCOPE,
        "bitcoin_excluded": True,
        "bitcoin_present": False,
        "spot_excluded": True,
        "synthetic_spot_excluded": True,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "universe_policy": UNIVERSE_POLICY,
        "universe_policy_id": UNIVERSE_POLICY_ID,
        "universe_policy_version": UNIVERSE_POLICY_VERSION,
        "universe_id": UNIVERSE_ID,
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "universe_lifecycle_registry_ref": UNIVERSE_LIFECYCLE_REGISTRY_REF,
        "lifecycle_registry_digest": RATIFIED_LIFECYCLE_REGISTRY_DIGEST,
        "instrument_identity_normalization": INSTRUMENT_ID_CANONICALIZATION_VERSION,
        "universe_digest": compute_universe_digest_v0(),
    }


def build_dataset_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "dataset_id": PANEL_DATASET_ID,
        "dataset_policy": DATASET_POLICY,
        "dataset_version": PANEL_DATASET_VERSION,
        "dataset_schema": PANEL_DATASET_SCHEMA,
        "panel_ohlcv_dataset_manifest_ref": PANEL_DATASET_MANIFEST_REF,
        "admissibility_manifest_ref": ADMISSIBILITY_MANIFEST_REF,
        "bar_interval": BAR_INTERVAL,
        "timestamp_alignment": TIMESTAMP_ALIGNMENT,
        "normalized_panel_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
        "panel_manifest_digest": RATIFIED_PANEL_MANIFEST_DIGEST,
        "dataset_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
        "data_contract_digest": compute_data_contract_digest_v0(),
        "finalized_bars_only": True,
        "forward_fill_forbidden": True,
        "dataset_rematerialization_required": False,
        "dataset_reuse": "REUSE_AS_IS",
    }


def build_period_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v1",
        "period_binding_id": PERIOD_BINDING_ID,
        "split_policy_id": PERIOD_BINDING_ID,
        "split_timezone": "UTC",
        "boundary_semantics": "utc_bar_close_inclusive_end",
        "warmup_start": "2024-05-25T00:00:00Z",
        "warmup_end": "2024-05-30T19:00:00Z",
        "training_start": "2024-05-30T20:00:00Z",
        "training_end": "2024-05-31T08:00:00Z",
        "validation_start": "2024-05-31T10:00:00Z",
        "validation_end": "2024-05-31T16:00:00Z",
        "out_of_sample_start": "2024-05-31T18:00:00Z",
        "out_of_sample_end": "2024-06-01T01:00:00Z",
        "embargo_duration": "PT2H",
        "purge_duration": "PT2H",
        "periods_frozen_before_evaluation": True,
        "no_overlap_enforced": True,
        "holdout_isolation_enforced": True,
        "period_split_reuse": "REUSE_AS_IS",
    }


def build_pit_contract_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "feature_time": "strictly_before_decision_time",
        "decision_time": "finalized_bar_close_epoch",
        "target_time": "strictly_after_decision_time",
        "feature_time_lt_decision_time": True,
        "target_time_gt_decision_time": True,
        "feature_time_gte_decision_time_forbidden": True,
        "target_time_lte_decision_time_forbidden": True,
        "same_bar_execution_forbidden": True,
        "contemporaneous_target_leakage_forbidden": True,
        "forward_fill_forbidden": True,
        "unfinalized_bars_forbidden": True,
        "signal_timing_policy": "finalized_bar_close_epoch",
        "survivorship_bias_forbidden": True,
        "future_universe_membership_forbidden": True,
    }


def build_cost_execution_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "cost_model_binding": "backtest_cost_stack_v0",
        "fee_binding": {
            "fee_model_version": FEE_MODEL_VERSION,
            "fee_bps_per_side": FEE_BPS_PER_SIDE,
        },
        "slippage_binding": {
            "slippage_model_version": SLIPPAGE_MODEL_VERSION,
            "slippage_bps_per_side": SLIPPAGE_BPS_PER_SIDE,
        },
        "funding_binding": {
            "funding_model_version": FUNDING_MODEL_VERSION,
            "bind": True,
        },
        "spread_binding": {
            "spread_model_version": SPREAD_MODEL_VERSION,
            "conservative_half_spread_bps": CONSERVATIVE_HALF_SPREAD_BPS,
        },
        "execution_model_binding": {
            "execution_model_version": EXECUTION_MODEL_VERSION,
            "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
            "effective_entry_cost_bps": EFFECTIVE_ENTRY_COST_BPS,
            "effective_exit_cost_bps": EFFECTIVE_EXIT_COST_BPS,
            "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
        },
        "implicit_zero_cost_forbidden": True,
    }


def build_economic_and_robustness_contract_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "economic_policy_binding": {
            "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
            "policy_lowering_forbidden": True,
            "promising_is_not_pass": True,
        },
        "walk_forward_contract": {
            "policy_version": WALK_FORWARD_POLICY_VERSION,
            "execution_forbidden_in_binding_scope": True,
        },
        "monte_carlo_contract": {
            "policy_version": MONTE_CARLO_POLICY_VERSION,
            "runs": MONTE_CARLO_RUNS,
            "seed": MONTE_CARLO_SEED,
            "execution_forbidden_in_binding_scope": True,
        },
        "stress_contract": {
            "policy_version": STRESS_POLICY_VERSION,
            "execution_forbidden_in_binding_scope": True,
        },
        "unchanged_retry_policy": {
            "unchanged_retry_blocked": True,
            "prior_binding_digest_unchanged_retry_forbidden": True,
            "lead_lag_v0_retry_forbidden": True,
            "policy_rescue_forbidden": True,
        },
    }


def build_score_family_policy_v0() -> dict[str, Any]:
    return {
        "schema_version": "score_family_policy.v0",
        "score_family_policy": SCORE_FAMILY_POLICY,
        "admissible_score_families": sorted(ADMISSIBLE_SCORE_FAMILIES),
        "forbidden_score_families": [PRIOR_LEAD_LAG_SCORE_FAMILY],
        "lead_lag_v0_score_family_reuse_forbidden": True,
        "unknown_score_family_rejected": True,
    }


def build_runner_decision_v0() -> dict[str, Any]:
    return {
        "schema_version": "runner_decision.v0",
        "runner_required": True,
        "runner_action": "DEFER_TO_SCORE_AND_RANKING_CONTRACT_IMPLEMENTATION_SCOPE",
        "evaluation_executed": False,
        "economic_evaluation_executed": False,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "next_operator_go": NEXT_OPERATOR_GO,
    }


def build_digest_dependency_graph_v0(
    *,
    config_digest: str,
    implementation_digest: str,
    material_difference_digest: str,
    binding_digest: str,
    data_digest: str,
    universe_digest: str,
    period_binding_digest: str,
) -> dict[str, Any]:
    return {
        "schema_version": "transitive_digest_graph.v0",
        "edges": [
            {"from": "parameter_binding", "to": "config_digest"},
            {"from": "pairwise_hypothesis_contract", "to": "config_digest"},
            {"from": "pit_universe_binding", "to": "config_digest"},
            {"from": "dataset_binding", "to": "config_digest"},
            {"from": "period_binding", "to": "config_digest"},
            {"from": "period_binding", "to": "period_binding_digest"},
            {"from": "pit_contract", "to": "config_digest"},
            {"from": "implementation_digest", "to": "binding_digest"},
            {"from": "config_digest", "to": "binding_digest"},
            {"from": "data_digest", "to": "binding_digest"},
            {"from": "material_difference_digest", "to": "binding_digest"},
            {"from": "universe_digest", "to": "binding_digest"},
            {"from": "period_binding_digest", "to": "binding_digest"},
            {"from": str(SOURCE_PARENT_EVALUATION_BUNDLE), "to": "material_difference_digest"},
        ],
        "component_digests": {
            "implementation_digest": implementation_digest,
            "config_digest": config_digest,
            "data_digest": data_digest,
            "dataset_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
            "universe_digest": universe_digest,
            "period_binding_digest": period_binding_digest,
            "material_difference_digest": material_difference_digest,
            "binding_digest": binding_digest,
        },
    }


def materialize_versioned_hypothesis_binding_v0() -> dict[str, Any]:
    parameter_binding = build_parameter_binding_v0()
    pairwise_contract = build_pairwise_hypothesis_contract_v0()
    pit_universe_binding = build_pit_universe_binding_v0()
    dataset_binding = build_dataset_binding_v0()
    period_binding = build_period_binding_v0()
    pit_contract = build_pit_contract_v0()
    pending_bindings = build_pending_implementation_bindings_v0()
    cost_binding = build_cost_execution_binding_v0()
    economic_robustness = build_economic_and_robustness_contract_v0()
    material_difference = build_material_difference_from_prior_v0()
    score_family_policy = build_score_family_policy_v0()

    config_digest = _stable_digest(
        {
            "parameter_binding": parameter_binding,
            "pairwise_hypothesis_contract": pairwise_contract,
            "pit_universe_binding": pit_universe_binding,
            "dataset_binding": dataset_binding,
            "period_binding": period_binding,
            "pit_contract": pit_contract,
            "pending_implementation_bindings": pending_bindings,
        }
    )
    implementation_digest = compute_implementation_digest_v0()
    data_digest = compute_data_contract_digest_v0()
    universe_digest = compute_universe_digest_v0()
    period_binding_digest = compute_period_binding_digest_v0(period_binding)
    material_difference_digest = compute_material_difference_digest_v0()
    binding_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "data_digest": data_digest,
            "implementation_digest": implementation_digest,
            "material_difference_digest": material_difference_digest,
            "period_binding_digest": period_binding_digest,
        }
    )

    binding: dict[str, Any] = {
        "binding_status": {
            "overall_binding_status": "COMPLETE",
            "universe_binding_status": "BOUND",
            "dataset_binding_status": "BOUND",
            "digest_binding_status": "BOUND",
            "period_binding_status": "BOUND",
            "pairwise_contract_binding_status": "BOUND",
            "pending_implementation_bindings_status": BOUND_PORTFOLIO_BINDING_STATUS,
            "portfolio_binding_scope": "COMPLETE",
            "cost_model_binding_status": "BOUND",
            "policy_classes_status": "BOUND",
        },
        "digest_bindings": {
            "config_digest": _field_bound(value=config_digest),
            "data_digest": _field_bound(value=data_digest),
            "dataset_digest": _field_bound(value=RATIFIED_NORMALIZED_PANEL_DIGEST),
            "universe_digest": _field_bound(value=universe_digest),
            "period_binding_digest": _field_bound(value=period_binding_digest),
            "implementation_digest": _field_bound(value=implementation_digest),
            "material_difference_digest": _field_bound(value=material_difference_digest),
            "binding_digest": _field_bound(value=binding_digest),
        },
        "external_bindings": {
            "pit_universe_manifest_ref": _field_bound(ref=PIT_UNIVERSE_MANIFEST_REF),
            "panel_ohlcv_dataset_manifest_ref": _field_bound(ref=PANEL_DATASET_MANIFEST_REF),
            "admissibility_manifest_ref": _field_bound(ref=ADMISSIBILITY_MANIFEST_REF),
            "evaluation_period_binding": _field_bound(ref=PERIOD_BINDING_REF),
            "fee_model_version": _field_bound(value=FEE_MODEL_VERSION),
            "slippage_model_version": _field_bound(value=SLIPPAGE_MODEL_VERSION),
            "funding_model_version": _field_bound(value=FUNDING_MODEL_VERSION),
            "spread_model_version": _field_bound(value=SPREAD_MODEL_VERSION),
            "execution_model_version": _field_bound(value=EXECUTION_MODEL_VERSION),
            "parent_terminal_evaluation_bundle_ref": _field_bound(
                ref=str(SOURCE_PARENT_EVALUATION_BUNDLE)
            ),
        },
        "parameter_binding": parameter_binding,
        "pairwise_hypothesis_contract": pairwise_contract,
        "pit_universe_binding": pit_universe_binding,
        "dataset_binding": dataset_binding,
        "period_binding": period_binding,
        "pit_contract": pit_contract,
        "pending_implementation_bindings": pending_bindings,
        "material_difference_from_prior": material_difference,
    }

    return {
        "artifact_kind": (
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding"
        ),
        "artifact_version": BINDING_ARTIFACT_VERSION,
        "schema_version": BINDING_SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_family": STRATEGY_FAMILY,
        "hypothesis_class": HYPOTHESIS_CLASS,
        "hypothesis_family": HYPOTHESIS_FAMILY,
        "research_hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "hypothesis_version": STRATEGY_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "hypothesis_statement": build_hypothesis_statement_v0(),
        "score_family_policy": SCORE_FAMILY_POLICY,
        "score_family_policy_contract": score_family_policy,
        "material_difference_proven": True,
        "same_semantic_binding": False,
        "binding": binding,
        "pairwise_hypothesis_contract": pairwise_contract,
        "pit_contract": pit_contract,
        "parameter_binding": parameter_binding,
        "pit_universe_binding": pit_universe_binding,
        "panel_dataset_binding": dataset_binding,
        "period_binding": period_binding,
        "pending_implementation_bindings": pending_bindings,
        "cost_execution_binding": cost_binding,
        "economic_and_robustness_contract": economic_robustness,
        "material_difference_from_prior": material_difference,
        "distinctness_and_negative_evidence_protection": {
            "prior_scope": PRIOR_LEAD_LAG_SCOPE,
            "prior_scope_status": PRIOR_LEAD_LAG_SCOPE_STATUS,
            "material_difference_proven": True,
            "material_difference_class": MATERIAL_DIFFERENCE_CLASS,
            "same_dataset_allowed": True,
            "same_mechanism": False,
            "same_score_family": False,
            "same_binding": False,
            "unchanged_retry": False,
            "negative_evidence_preserved": True,
            "policy_rescue": False,
        },
        "implementation_digest": implementation_digest,
        "config_digest": config_digest,
        "data_digest": data_digest,
        "dataset_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
        "universe_digest": universe_digest,
        "period_binding_digest": period_binding_digest,
        "material_difference_digest": material_difference_digest,
        "binding_digest": binding_digest,
        "binding_classification": "PORTFOLIO_BINDING_COMPLETION_V0",
        "supersession_mode": SUPERSESSION_MODE,
        "pre_ratified_binding_digest": PRE_RATIFIED_BINDING_DIGEST,
        "portfolio_binding_go_token": PORTFOLIO_BINDING_GO_TOKEN,
        "semantic_binding_fields_changed": True,
        "cryptographic_binding_identity_changed": True,
        "orchestrator_owner": ORCHESTRATOR_OWNER,
        "runner_decision": build_runner_decision_v0(),
        "digest_dependency_graph": build_digest_dependency_graph_v0(
            config_digest=config_digest,
            implementation_digest=implementation_digest,
            material_difference_digest=material_difference_digest,
            binding_digest=binding_digest,
            data_digest=data_digest,
            universe_digest=universe_digest,
            period_binding_digest=period_binding_digest,
        ),
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "bitcoin_present": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
            "spot_excluded": True,
            "synthetic_spot_excluded": True,
            "offline_only": True,
            "no_runtime": True,
            "no_economic_evaluation": True,
            "prior_lead_lag_binding_not_reused_unchanged": True,
            "unchanged_retry_blocked": True,
            "policy_rescue_forbidden": True,
            "dataset_rematerialization_required": False,
            "dataset_reuse": "REUSE_AS_IS",
            "universe_reuse": "REUSE_AS_IS",
            "period_split_reuse": "REUSE_AS_IS",
        },
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "economic_evaluation_executed": False,
    }


def validate_score_family_policy_v0(score_family: str) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if score_family not in ADMISSIBLE_SCORE_FAMILIES:
        reasons.append("UNKNOWN_SCORE_FAMILY")
    if score_family == PRIOR_LEAD_LAG_SCORE_FAMILY:
        reasons.append("LEAD_LAG_V0_SCORE_FAMILY_REUSED")
    return not reasons, tuple(dict.fromkeys(reasons))


def validate_versioned_hypothesis_binding_v0(
    envelope: Mapping[str, Any],
) -> tuple[BindingValidationVerdict, tuple[str, ...]]:
    reasons: list[str] = []
    binding = envelope.get("binding", {})
    if binding.get("binding_status", {}).get("overall_binding_status") != "COMPLETE":
        reasons.append("BINDING_INCOMPLETE")
    if envelope.get("binding_digest") != binding.get("digest_bindings", {}).get(
        "binding_digest", {}
    ).get("value"):
        reasons.append("BINDING_DIGEST_MISMATCH")
    if envelope.get("binding_digest") == PRIOR_LEAD_LAG_BINDING_DIGEST:
        reasons.append("PRIOR_LEAD_LAG_BINDING_DIGEST_REUSED")
    if envelope.get("same_semantic_binding") is not False:
        reasons.append("SAME_SEMANTIC_BINDING_NOT_FALSE")
    if envelope.get("material_difference_proven") is not True:
        reasons.append("MATERIAL_DIFFERENCE_NOT_PROVEN")

    score_ok, score_reasons = validate_score_family_policy_v0(
        str(envelope.get("score_family_policy", ""))
    )
    if not score_ok:
        reasons.extend(score_reasons)
    if envelope.get("score_family_policy") != SCORE_FAMILY_POLICY:
        reasons.append("SCORE_FAMILY_POLICY_MISMATCH")

    digests = binding.get("digest_bindings", {})
    if digests.get("dataset_digest", {}).get("value") != RATIFIED_NORMALIZED_PANEL_DIGEST:
        reasons.append("DATASET_DIGEST_MISMATCH")
    if not digests.get("universe_digest", {}).get("value"):
        reasons.append("MISSING_UNIVERSE_BINDING")
    if not digests.get("period_binding_digest", {}).get("value"):
        reasons.append("MISSING_PERIOD_BINDING")
    if not digests.get("data_digest", {}).get("value"):
        reasons.append("MISSING_DATASET_BINDING")

    constraints = envelope.get("system_constraints", {})
    if constraints.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if constraints.get("unchanged_retry_blocked") is not True:
        reasons.append("UNCHANGED_RETRY_BLOCK_VIOLATION")

    pairwise = envelope.get("pairwise_hypothesis_contract", {})
    if pairwise.get("finalized_bars_only") is not True:
        reasons.append("UNFINALIZED_BARS_ALLOWED")
    if pairwise.get("forward_fill_forbidden") is not True:
        reasons.append("FORWARD_FILL_ALLOWED")
    if pairwise.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_ALLOWED")
    if pairwise.get("spot_allowed") is not False:
        reasons.append("SPOT_ALLOWED")
    if pairwise.get("synthetic_spot_allowed") is not False:
        reasons.append("SYNTHETIC_SPOT_ALLOWED")
    if pairwise.get("panel_median_benchmark_semantics_forbidden") is not True:
        reasons.append("PANEL_MEDIAN_BENCHMARK_NOT_FORBIDDEN")
    if pairwise.get("lead_lag_v0_binding_reuse_forbidden") is not True:
        reasons.append("LEAD_LAG_V0_BINDING_REUSE_NOT_FORBIDDEN")

    pit = envelope.get("pit_contract", {})
    if pit.get("feature_time_lt_decision_time") is not True:
        reasons.append("FEATURE_TIME_ORDERING_VIOLATION")
    if pit.get("target_time_gt_decision_time") is not True:
        reasons.append("TARGET_TIME_ORDERING_VIOLATION")
    if pit.get("feature_time_gte_decision_time_forbidden") is not True:
        reasons.append("FEATURE_TIME_GTE_DECISION_NOT_FORBIDDEN")
    if pit.get("target_time_lte_decision_time_forbidden") is not True:
        reasons.append("TARGET_TIME_LTE_DECISION_NOT_FORBIDDEN")
    if pit.get("unfinalized_bars_forbidden") is not True:
        reasons.append("UNFINALIZED_BARS_ALLOWED")

    pending = envelope.get("pending_implementation_bindings", {})
    portfolio_ok, portfolio_reasons = validate_portfolio_implementation_bindings_v0(pending)
    if not portfolio_ok:
        reasons.extend(portfolio_reasons)
    if pending.get("portfolio_binding_scope") != "COMPLETE":
        reasons.append("PORTFOLIO_BINDING_SCOPE_INCOMPLETE")

    negative = envelope.get("distinctness_and_negative_evidence_protection", {})
    if negative.get("negative_evidence_preserved") is not True:
        reasons.append("NEGATIVE_EVIDENCE_NOT_PRESERVED")
    if negative.get("policy_rescue") is not False:
        reasons.append("POLICY_RESCUE_NOT_FALSE")
    if negative.get("unchanged_retry") is not False:
        reasons.append("UNCHANGED_RETRY_NOT_FALSE")

    unique = tuple(dict.fromkeys(reasons))
    if unique:
        return BindingValidationVerdict.REJECTED_INCOMPLETE, unique
    return BindingValidationVerdict.ACCEPTED_COMPLETE, ()


def validate_pairwise_contract_rejections_v0(
    envelope: Mapping[str, Any],
    *,
    mutated_field: str,
    mutated_value: Any,
) -> tuple[bool, tuple[str, ...]]:
    mutated = deepcopy(dict(envelope))
    if mutated_field.startswith("pit."):
        mutated.setdefault("pit_contract", {})[mutated_field.split(".", 1)[1]] = mutated_value
        mutated.setdefault("binding", {})["pit_contract"] = mutated["pit_contract"]
    elif mutated_field.startswith("pairwise."):
        mutated.setdefault("pairwise_hypothesis_contract", {})[mutated_field.split(".", 1)[1]] = (
            mutated_value
        )
        mutated.setdefault("binding", {})["pairwise_hypothesis_contract"] = mutated[
            "pairwise_hypothesis_contract"
        ]
    else:
        mutated[mutated_field] = mutated_value
    verdict, reasons = validate_versioned_hypothesis_binding_v0(mutated)
    return verdict is BindingValidationVerdict.REJECTED_INCOMPLETE, reasons


def validate_prior_lead_lag_not_reused_unchanged_v0(
    envelope: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    binding_digest = envelope.get("binding_digest")
    if binding_digest == PRIOR_LEAD_LAG_BINDING_DIGEST:
        reasons.append("PRIOR_LEAD_LAG_BINDING_DIGEST_REUSED")
    material = envelope.get("material_difference_from_prior", {})
    if material.get("prior_binding_not_reused_unchanged") is not True:
        reasons.append("PRIOR_LEAD_LAG_BINDING_REUSE_FLAG_FALSE")
    if material.get("negative_evidence_preserved") is not True:
        reasons.append("NEGATIVE_EVIDENCE_NOT_PRESERVED")
    if envelope.get("score_family_policy") == PRIOR_LEAD_LAG_SCORE_FAMILY:
        reasons.append("PRIOR_LEAD_LAG_SCORE_FAMILY_REUSED")
    return not reasons, tuple(dict.fromkeys(reasons))


def materialize_and_validate_versioned_hypothesis_binding_v0() -> (
    VersionedHypothesisBindingResultV0
):
    envelope = materialize_versioned_hypothesis_binding_v0()
    validation_verdict, fail_reasons = validate_versioned_hypothesis_binding_v0(envelope)
    verdict = (
        BindingMaterializationVerdict.COMPLETE
        if validation_verdict is BindingValidationVerdict.ACCEPTED_COMPLETE
        else BindingMaterializationVerdict.INCOMPLETE
    )
    return VersionedHypothesisBindingResultV0(
        verdict=verdict,
        validation_verdict=validation_verdict,
        binding=envelope,
        fail_reasons=fail_reasons,
    )


def serialize_versioned_hypothesis_binding_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(envelope, indent=2, sort_keys=True) + "\n"


def materializer_to_binder_roundtrip_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    roundtrip = json.loads(serialize_versioned_hypothesis_binding_json_v0(envelope))
    validation_verdict, fail_reasons = validate_versioned_hypothesis_binding_v0(roundtrip)
    return {
        "materializer_to_binder_roundtrip_pass": (
            validation_verdict is BindingValidationVerdict.ACCEPTED_COMPLETE
            and roundtrip.get("binding_digest") == envelope.get("binding_digest")
        ),
        "validation_verdict": validation_verdict.value,
        "fail_reasons": list(fail_reasons),
    }


def compare_materialization_envelopes_v0(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
) -> tuple[bool, dict[str, Any]]:
    if first == second:
        return True, {}
    return False, {"diff_keys": sorted(set(first) ^ set(second))}


def build_owner_inventory() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v0",
        "research_scope_ratification_owner": (
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
            "research_scope_ratification_v0"
        ),
        "hypothesis_config_owner": CONFIG_REL_PATH,
        "versioned_hypothesis_binding_owner": VALIDATOR_OWNER,
        "score_family_policy_owner": VALIDATOR_OWNER,
        "dataset_binding_owner": "src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1",
        "universe_binding_owner": "pit_futures_universe_manifest_v1",
        "period_binding_owner": PERIOD_BINDING_ID,
        "ranking_semantics_binding_owner": "DEFERRED_PENDING_IMPLEMENTATION_SCOPE",
        "pairwise_relation_contract_owner": VALIDATOR_OWNER,
        "cost_execution_binding_owner": "backtest_cost_models_v0",
        "economic_policy_binding_owner": "src.backtest.economic_validity_policy_v1",
        "digest_owner": VALIDATOR_OWNER,
        "materializer_owner": MATERIALIZER_OWNER,
        "binder_validator_owner": VALIDATOR_OWNER,
        "manifest_owner": MANIFEST_OWNER,
        "registry_progress_owner": ORCHESTRATOR_OWNER,
        "tests_owner": (
            "tests.research."
            "test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
            "versioned_hypothesis_binding_v0_contract"
        ),
        "evidence_materializer_owner": MATERIALIZER_OWNER,
        "downstream_canonical_entry_point": "DEFERRED_PENDING_SCORE_IMPLEMENTATION_SCOPE",
        "parallel_owner_created": False,
    }


def build_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "decision_ladder": "REUSE_AS_IS -> REUSE_WITH_NARROW_ADAPTER",
        "dataset_panel_owner": "src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1",
        "pit_universe_owner": "pit_futures_universe_manifest_v1",
        "period_binding_owner": PERIOD_BINDING_ID,
        "orchestrator_owner": ORCHESTRATOR_OWNER,
        "cost_stack_owner": "backtest_cost_models_v0",
        "dataset_reuse": "REUSE_AS_IS",
        "universe_reuse": "REUSE_AS_IS",
        "period_split_reuse": "REUSE_AS_IS",
        "dataset_rematerialization_required": False,
        "prior_lead_lag_binding_reference_only": True,
        "prior_lead_lag_binding_not_reused_unchanged": True,
        "new_score_owner_required": True,
        "new_parallel_owner_created": False,
    }


def build_field_classification_v0() -> dict[str, Any]:
    return {
        "schema_version": "field_classification.v0",
        "semantic_strategy_fields": [
            "hypothesis_statement",
            "hypothesis_family",
            "score_family_policy",
            "pair_definition",
            "leader_feature_family",
            "follower_target_family",
        ],
        "semantic_pairwise_fields": [
            "pairwise_relation_output",
            "graph_output",
            "node_semantics",
            "edge_semantics",
        ],
        "semantic_timing_fields": [
            "feature_time_lt_decision_time",
            "target_time_gt_decision_time",
            "contemporaneous_target_leakage_forbidden",
        ],
        "portfolio_policy_fields": [
            "aggregation_policy",
            "selection_policy",
            "holding_policy",
            "exit_policy",
            "portfolio_weighting_policy",
        ],
        "cryptographic_dataset_fields": ["dataset_digest", "data_digest", "universe_digest"],
        "cryptographic_binding_fields": [
            "binding_digest",
            "config_digest",
            "implementation_digest",
            "period_binding_digest",
            "material_difference_digest",
        ],
        "supersession_fields": [
            "parent_terminal_evaluation_bundle",
            "prior_lead_lag_binding_digest",
            "negative_evidence_preserved",
        ],
        "unclassified_changed_field_count": 0,
    }


def build_semantic_identity_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "semantic_identity.v0",
        "research_scope": envelope["research_scope"],
        "hypothesis_id": envelope["hypothesis_id"],
        "hypothesis_family": envelope["hypothesis_family"],
        "score_family_policy": envelope["score_family_policy"],
        "pair_definition": envelope["parameter_binding"]["pair_definition"],
        "graph_output": envelope["parameter_binding"]["graph_output"],
        "same_semantic_binding": False,
        "semantic_identity_independent": True,
    }


def build_cryptographic_identity_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "cryptographic_identity.v0",
        "binding_digest": envelope["binding_digest"],
        "config_digest": envelope["config_digest"],
        "implementation_digest": envelope["implementation_digest"],
        "data_digest": envelope["data_digest"],
        "dataset_digest": envelope["dataset_digest"],
        "universe_digest": envelope["universe_digest"],
        "period_binding_digest": envelope["period_binding_digest"],
        "material_difference_digest": envelope["material_difference_digest"],
        "prior_lead_lag_binding_digest": PRIOR_LEAD_LAG_BINDING_DIGEST,
        "cryptographic_binding_identity_changed": (
            envelope["binding_digest"] != PRIOR_LEAD_LAG_BINDING_DIGEST
        ),
    }


def build_before_after_field_diff_v0(
    *,
    prior_envelope: Mapping[str, Any],
    new_envelope: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    compare = (
        (
            "score_family_policy",
            prior_envelope.get("score_family_policy"),
            new_envelope.get("score_family_policy"),
        ),
        (
            "hypothesis_family",
            prior_envelope.get("strategy_family"),
            new_envelope.get("hypothesis_family"),
        ),
        (
            "binding_digest",
            prior_envelope.get("binding_digest"),
            new_envelope.get("binding_digest"),
        ),
        (
            "research_scope",
            prior_envelope.get("research_scope"),
            new_envelope.get("research_scope"),
        ),
        (
            "pair_definition",
            None,
            new_envelope.get("parameter_binding", {}).get("pair_definition"),
        ),
        (
            "graph_output",
            None,
            new_envelope.get("parameter_binding", {}).get("graph_output"),
        ),
    )
    for field, prior_val, new_val in compare:
        if prior_val != new_val:
            rows.append(
                {
                    "field": field,
                    "prior_value": prior_val,
                    "new_value": new_val,
                    "change_type": "EXPECTED_MATERIAL_HYPOTHESIS_CHANGE",
                }
            )
    return rows


def build_semantic_identity_comparison_v0(
    *,
    prior_envelope: Mapping[str, Any],
    new_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    diff_rows = build_before_after_field_diff_v0(
        prior_envelope=prior_envelope, new_envelope=new_envelope
    )
    return {
        "schema_version": "semantic_identity_comparison.v0",
        "distinct_hypothesis": True,
        "semantic_binding_fields_changed": len(diff_rows) > 0,
        "changed_fields": [row["field"] for row in diff_rows],
        "prior_scope": prior_envelope.get("research_scope"),
        "new_scope": new_envelope.get("research_scope"),
        "prior_score_family": prior_envelope.get("score_family_policy"),
        "new_score_family": new_envelope.get("score_family_policy"),
    }


def build_cryptographic_identity_comparison_v0(
    *,
    prior_envelope: Mapping[str, Any],
    new_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "cryptographic_identity_comparison.v0",
        "prior_binding_digest": prior_envelope.get("binding_digest"),
        "new_binding_digest": new_envelope.get("binding_digest"),
        "cryptographic_binding_identity_changed": (
            prior_envelope.get("binding_digest") != new_envelope.get("binding_digest")
        ),
        "prior_data_digest": prior_envelope.get("data_digest"),
        "new_data_digest": new_envelope.get("data_digest"),
        "cryptographic_dataset_identity_unchanged": (
            prior_envelope.get("data_digest") == new_envelope.get("data_digest")
        ),
        "cryptographic_distinctness_proven": (
            prior_envelope.get("binding_digest") != new_envelope.get("binding_digest")
        ),
    }
