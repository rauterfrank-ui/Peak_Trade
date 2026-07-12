"""Versioned hypothesis binding for cross_sectional_futures_lead_lag_information_diffusion/v0.

Binds the ratified panel-median-benchmark lagged return diffusion hypothesis on the
canonical PIT OHLCV cross-sectional panel. Research-only; no runtime or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    ADMISSIBLE_LAG_SURFACE,
    DEFAULT_LAG_WINDOW_L,
    DEFAULT_SIGNAL_LAG_BARS,
    MIN_ELIGIBLE_MEMBERS,
    SCORE_FORMULA_EXPRESSION,
    SCORE_FORMULA_VERSION,
)
from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    MANIFEST_ARTIFACT_ID,
    UNIVERSE_ID,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_VERSIONED_HYPOTHESIS_BINDING_V0=true"
)
BINDING_ARTIFACT_VERSION = "v0"
BINDING_SCHEMA_VERSION = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding.v0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_"
    "versioned_hypothesis_binding_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_"
    "VERSIONED_HYPOTHESIS_BINDING_V0.md"
)
CONFIRM_GO = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_"
    "VERSIONED_HYPOTHESIS_BINDING_RATIFICATION_V0"
)
MATERIALIZATION_CONFIRM_GO = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_"
    "VERSIONED_HYPOTHESIS_BINDING_MATERIALIZATION_V0"
)
REQUIRED_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "preflight.txt",
    "source_manifest_verification.txt",
    "transitive_manifest_verification.txt",
    "canonical_owner_inventory.json",
    "reuse_decision.json",
    "field_classification.json",
    "binding_source_inputs.json",
    "materialized_binding.json",
    "digest_contracts.json",
    "digest_dependency_graph.json",
    "before_after_field_diff.json",
    "semantic_identity_comparison.json",
    "cryptographic_identity_comparison.json",
    "materializer_roundtrip.txt",
    "deterministic_materialization.txt",
    "binder_validation.txt",
    "test_assertion_matrix.json",
    "test_results.txt",
    "ci_mode_decision.json",
    "final_report.txt",
    "MANIFEST.sha256",
    "MANIFEST.verify.txt",
)

STRATEGY_ID = "cross_sectional_futures_lead_lag_information_diffusion"
STRATEGY_VERSION = "v0"
HYPOTHESIS_CLASS = "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION"
RESEARCH_HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_NON_BITCOIN_PERPETUALS_V0"
)
RESEARCH_SCOPE = "cross_sectional_futures_lead_lag_information_diffusion/v0"
STRATEGY_FAMILY = "cross_sectional_panel_lag_diffusion"

PANEL_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
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

PRIOR_RELATIVE_STRENGTH_SCOPE = "cross_sectional_relative_strength/v0"
PRIOR_RELATIVE_STRENGTH_HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"
)
PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST = (
    "84148813b30300eebb4ead67fdf680974181b417c89380ac4a6c368b6d61b70e"
)
PRIOR_RELATIVE_STRENGTH_SCORE_FAMILY = "volatility_normalized_fixed_lookback_return"

SCORE_FAMILY_POLICY = "panel_median_benchmark_lagged_return_diffusion_v0"
SELECTION_MODE = "single_top1_by_score_desc"
RANKING_FORMULA = "rank_by_panel_median_lagged_return_diffusion_v0"
RANKING_DIRECTION = "symmetric_top1_long_laggard_short_leader_v0"
DETERMINISTIC_TIE_BREAK = "score_desc_then_instrument_id_asc"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_FEASIBILITY_BUNDLE = (
    DURABLE_ARCHIVE_ROOT / "planning/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_contract_and_"
    "dataset_feasibility_read_only_v0_20260712T195800Z"
)
SOURCE_RATIFICATION_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT / "planning/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_full_canonical_system_"
    "post_completion_versioned_binding_ratification_read_only_v0_20260712T232909Z"
)

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
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_"
    "OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
NEXT_OPERATOR_GO = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_"
    "OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)

ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"
MANIFEST_OWNER = "scripts.ops.primary_evidence_retention_v0"
MATERIALIZER_OWNER = (
    "scripts.research."
    "materialize_cross_sectional_futures_lead_lag_information_diffusion_v0_"
    "versioned_hypothesis_binding_v0"
)
VALIDATOR_OWNER = (
    "src.research."
    "cross_sectional_futures_lead_lag_information_diffusion_v0_"
    "versioned_hypothesis_binding_v0"
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


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": (
                "cross_sectional_futures_lead_lag_information_diffusion_v0_"
                "versioned_hypothesis_binding_v0"
            ),
            "orchestrator": ORCHESTRATOR_OWNER,
            "score_formula_version": SCORE_FORMULA_VERSION,
            "score_family_policy": SCORE_FAMILY_POLICY,
            "schema_version": BINDING_SCHEMA_VERSION,
        }
    )


def compute_data_contract_digest_v0() -> str:
    return _stable_digest(
        {
            "dataset_id": PANEL_DATASET_ID,
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


def compute_material_difference_digest_v0() -> str:
    return _stable_digest(
        {
            "prior_relative_strength_scope": PRIOR_RELATIVE_STRENGTH_SCOPE,
            "prior_relative_strength_score_family": PRIOR_RELATIVE_STRENGTH_SCORE_FAMILY,
            "new_score_family": SCORE_FAMILY_POLICY,
            "distinct_hypothesis": True,
            "same_semantic_binding": False,
            "unchanged_retry": False,
            "panel_median_lag_diffusion": True,
        }
    )


def build_hypothesis_statement_v0() -> str:
    return (
        "Cross-sectional futures lead-lag information diffusion hypothesis: rank instruments "
        "by panel-median-benchmark lagged return diffusion score on finalized PT1H OHLCV; "
        "long laggards and short leaders via symmetric single-slot top1 rotation."
    )


def build_material_difference_from_prior_v0() -> dict[str, Any]:
    return {
        "material_difference_proven": True,
        "same_semantic_binding": False,
        "prior_relative_strength_scope": PRIOR_RELATIVE_STRENGTH_SCOPE,
        "prior_relative_strength_hypothesis_id": PRIOR_RELATIVE_STRENGTH_HYPOTHESIS_ID,
        "prior_relative_strength_score_family": PRIOR_RELATIVE_STRENGTH_SCORE_FAMILY,
        "prior_relative_strength_binding_digest": PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST,
        "new_score_family_policy": SCORE_FAMILY_POLICY,
        "new_ranking_formula": RANKING_FORMULA,
        "mechanism_delta": (
            "contemporaneous_volatility_normalized_return_rank vs "
            "lagged_panel_median_diffusion_score"
        ),
        "temporal_structure_delta": (
            "single_lookback_momentum vs multi_instrument_information_diffusion_lag"
        ),
        "prior_binding_not_reused_unchanged": True,
        "unchanged_retry_blocked": True,
        "source_feasibility_bundle": str(SOURCE_FEASIBILITY_BUNDLE),
    }


def build_parameter_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "lag_window_L": DEFAULT_LAG_WINDOW_L,
        "admissible_lag_surface_bars": list(ADMISSIBLE_LAG_SURFACE),
        "lag_window_optimization_forbidden": True,
        "signal_lag_bars": DEFAULT_SIGNAL_LAG_BARS,
        "rebalance_interval_bars": 1,
        "switch_entry_delay_epochs": 1,
        "max_bar_staleness_bars": 1,
        "min_eligible_members_for_rank": MIN_ELIGIBLE_MEMBERS,
        "minimum_history_bars": DEFAULT_LAG_WINDOW_L + DEFAULT_SIGNAL_LAG_BARS,
        "score_formula_version": SCORE_FORMULA_VERSION,
        "score_formula_expression": SCORE_FORMULA_EXPRESSION,
        "parameter_search_forbidden": True,
        "prior_relative_strength_binding_not_reused_unchanged": True,
        "unchanged_retry_of_failed_bindings_forbidden": True,
    }


def build_pit_universe_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "venue": "OKX",
        "instrument_type": "LINEAR_PERPETUAL",
        "settlement_asset": "USDT",
        "bitcoin_excluded": True,
        "bitcoin_present": False,
        "spot_excluded": True,
        "synthetic_spot_excluded": True,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "universe_policy_id": UNIVERSE_POLICY_ID,
        "universe_policy_version": UNIVERSE_POLICY_VERSION,
        "universe_id": UNIVERSE_ID,
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "universe_lifecycle_registry_ref": UNIVERSE_LIFECYCLE_REGISTRY_REF,
        "lifecycle_registry_digest": RATIFIED_LIFECYCLE_REGISTRY_DIGEST,
        "minimum_eligible_member_count": MIN_ELIGIBLE_MEMBERS,
        "minimum_history_bars": DEFAULT_LAG_WINDOW_L + DEFAULT_SIGNAL_LAG_BARS,
        "instrument_identity_normalization": INSTRUMENT_ID_CANONICALIZATION_VERSION,
        "universe_digest": compute_universe_digest_v0(),
    }


def build_dataset_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "dataset_id": PANEL_DATASET_ID,
        "dataset_version": PANEL_DATASET_VERSION,
        "dataset_schema": PANEL_DATASET_SCHEMA,
        "panel_ohlcv_dataset_manifest_ref": PANEL_DATASET_MANIFEST_REF,
        "admissibility_manifest_ref": ADMISSIBILITY_MANIFEST_REF,
        "bar_interval": "PT1H",
        "normalized_panel_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
        "panel_manifest_digest": RATIFIED_PANEL_MANIFEST_DIGEST,
        "dataset_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
        "data_contract_digest": compute_data_contract_digest_v0(),
        "finalized_bars_only": True,
        "panel_alignment_semantics": "common_utc_hourly_close_intersection_no_forward_fill",
    }


def build_ranking_policy_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "score_family_policy": SCORE_FAMILY_POLICY,
        "ranking_formula": RANKING_FORMULA,
        "ranking_direction": RANKING_DIRECTION,
        "selection_mode": SELECTION_MODE,
        "deterministic_tie_break": DETERMINISTIC_TIE_BREAK,
        "tie_break_score_source": "unrounded_internal_score",
        "leader_semantics": "highest_lagged_return_at_feature_time",
        "laggard_semantics": "lowest_lagged_return_at_feature_time",
        "long_top1_means": "LONG_LAGGARD",
        "short_top1_means": "SHORT_LEADER",
        "minimum_rankable_instrument_count": MIN_ELIGIBLE_MEMBERS,
        "missing_instrument_policy": "exclude_non_selected_for_epoch",
        "stale_instrument_policy": "exclude_when_staleness_exceeds_max_bar_staleness_bars",
        "insufficient_history_policy": "exclude_instrument_for_epoch",
        "insufficient_panel_policy": "FLAT",
        "finalized_bar_only": True,
    }


def build_selection_hold_exit_rotation_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "selection_count": 1,
        "rebalance_interval_bars": 1,
        "rebalance_policy_class": "fixed_N_bar_cadence",
        "hold_semantics": "until_next_rebalance",
        "exit_semantics": "rotation_via_switch_policy_flat_then_wait_one_epoch",
        "switch_policy": "flat_then_wait_one_epoch_then_enter",
        "switch_entry_delay_epochs": 1,
        "cooldown_policy": "no_cooldown",
        "end_of_window_policy": "force_close_at_window_end_inclusive_v0",
        "weighting_policy": "equal_weight_single_slot_v0",
        "gross_exposure_policy": "unit_notional_single_slot_v0",
        "net_exposure_policy": "directional_single_slot_v0",
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
        },
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
    }


def build_pit_contract_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "feature_time": "t_decision - signal_lag_bars * PT1H",
        "decision_time": "finalized_bar_close_epoch",
        "target_time": "next_rebalance_epoch_close",
        "feature_time_lt_decision_time": True,
        "target_time_gt_decision_time": True,
        "same_bar_execution_forbidden": True,
        "signal_timing_policy": "finalized_bar_close_epoch",
        "survivorship_bias_forbidden": True,
        "future_universe_membership_forbidden": True,
        "contemporaneous_target_leakage_forbidden": True,
    }


def build_runner_decision_v0() -> dict[str, Any]:
    return {
        "schema_version": "runner_decision.v0",
        "runner_required": True,
        "runner_action": "DEFER_TO_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE",
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
) -> dict[str, Any]:
    return {
        "schema_version": "transitive_digest_graph.v0",
        "edges": [
            {"from": "parameter_binding", "to": "config_digest"},
            {"from": "pit_universe_binding", "to": "config_digest"},
            {"from": "dataset_binding", "to": "config_digest"},
            {"from": "ranking_policy_binding", "to": "config_digest"},
            {"from": "selection_hold_exit_rotation_binding", "to": "config_digest"},
            {"from": "period_binding", "to": "config_digest"},
            {"from": "pit_contract", "to": "config_digest"},
            {"from": "implementation_digest", "to": "binding_digest"},
            {"from": "config_digest", "to": "binding_digest"},
            {"from": "data_digest", "to": "binding_digest"},
            {"from": "material_difference_digest", "to": "binding_digest"},
            {"from": "universe_digest", "to": "binding_digest"},
            {"from": str(SOURCE_FEASIBILITY_BUNDLE), "to": "material_difference_digest"},
        ],
        "component_digests": {
            "implementation_digest": implementation_digest,
            "config_digest": config_digest,
            "data_digest": data_digest,
            "dataset_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
            "universe_digest": universe_digest,
            "material_difference_digest": material_difference_digest,
            "binding_digest": binding_digest,
        },
    }


def materialize_versioned_hypothesis_binding_v0() -> dict[str, Any]:
    parameter_binding = build_parameter_binding_v0()
    pit_universe_binding = build_pit_universe_binding_v0()
    dataset_binding = build_dataset_binding_v0()
    ranking_policy_binding = build_ranking_policy_binding_v0()
    selection_binding = build_selection_hold_exit_rotation_binding_v0()
    period_binding = build_period_binding_v0()
    pit_contract = build_pit_contract_v0()
    cost_binding = build_cost_execution_binding_v0()
    economic_robustness = build_economic_and_robustness_contract_v0()
    material_difference = build_material_difference_from_prior_v0()

    config_digest = _stable_digest(
        {
            "parameter_binding": parameter_binding,
            "pit_universe_binding": pit_universe_binding,
            "dataset_binding": dataset_binding,
            "ranking_policy_binding": ranking_policy_binding,
            "selection_hold_exit_rotation_binding": selection_binding,
            "period_binding": period_binding,
            "pit_contract": pit_contract,
        }
    )
    implementation_digest = compute_implementation_digest_v0()
    data_digest = compute_data_contract_digest_v0()
    universe_digest = compute_universe_digest_v0()
    material_difference_digest = compute_material_difference_digest_v0()
    binding_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "data_digest": data_digest,
            "implementation_digest": implementation_digest,
            "material_difference_digest": material_difference_digest,
        }
    )

    binding: dict[str, Any] = {
        "binding_status": {
            "overall_binding_status": "COMPLETE",
            "universe_binding_status": "BOUND",
            "dataset_binding_status": "BOUND",
            "digest_binding_status": "BOUND",
            "numeric_bindings_status": "BOUND",
            "cost_model_binding_status": "BOUND",
            "period_binding_status": "BOUND",
            "policy_classes_status": "BOUND",
            "ranking_policy_binding_status": "BOUND",
            "selection_hold_exit_rotation_binding_status": "BOUND",
        },
        "digest_bindings": {
            "config_digest": _field_bound(value=config_digest),
            "data_digest": _field_bound(value=data_digest),
            "dataset_digest": _field_bound(value=RATIFIED_NORMALIZED_PANEL_DIGEST),
            "universe_digest": _field_bound(value=universe_digest),
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
            "source_feasibility_bundle_ref": _field_bound(ref=str(SOURCE_FEASIBILITY_BUNDLE)),
        },
        "parameter_binding": parameter_binding,
        "pit_universe_binding": pit_universe_binding,
        "dataset_binding": dataset_binding,
        "ranking_policy_binding": ranking_policy_binding,
        "selection_hold_exit_rotation_binding": selection_binding,
        "period_binding": period_binding,
        "pit_contract": pit_contract,
        "material_difference_from_prior": material_difference,
    }

    return {
        "artifact_kind": (
            "cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding"
        ),
        "artifact_version": BINDING_ARTIFACT_VERSION,
        "schema_version": BINDING_SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_family": STRATEGY_FAMILY,
        "hypothesis_class": HYPOTHESIS_CLASS,
        "research_hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "hypothesis_version": STRATEGY_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "hypothesis_statement": build_hypothesis_statement_v0(),
        "score_family_policy": SCORE_FAMILY_POLICY,
        "score_definition": SCORE_FORMULA_EXPRESSION,
        "material_difference_proven": True,
        "same_semantic_binding": False,
        "binding": binding,
        "pit_contract": pit_contract,
        "parameter_binding": parameter_binding,
        "pit_universe_binding": pit_universe_binding,
        "panel_dataset_binding": dataset_binding,
        "ranking_policy_binding": ranking_policy_binding,
        "selection_hold_exit_rotation_binding": selection_binding,
        "period_binding": period_binding,
        "cost_execution_binding": cost_binding,
        "economic_and_robustness_contract": economic_robustness,
        "material_difference_from_prior": material_difference,
        "implementation_digest": implementation_digest,
        "config_digest": config_digest,
        "data_digest": data_digest,
        "dataset_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
        "universe_digest": universe_digest,
        "binding_digest": binding_digest,
        "binding_classification": "NEW_DISTINCT_HYPOTHESIS_LAG_DIFFUSION_SCORE_FAMILY",
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
        ),
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "bitcoin_present": False,
            "spot_excluded": True,
            "synthetic_spot_excluded": True,
            "offline_only": True,
            "no_runtime": True,
            "no_economic_evaluation": True,
            "prior_relative_strength_binding_not_reused_unchanged": True,
            "unchanged_retry_blocked": True,
        },
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "economic_evaluation_executed": False,
    }


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
    if envelope.get("binding_digest") == PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST:
        reasons.append("PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST_REUSED")
    if envelope.get("same_semantic_binding") is not False:
        reasons.append("SAME_SEMANTIC_BINDING_NOT_FALSE")
    if envelope.get("material_difference_proven") is not True:
        reasons.append("MATERIAL_DIFFERENCE_NOT_PROVEN")
    if envelope.get("score_family_policy") != SCORE_FAMILY_POLICY:
        reasons.append("SCORE_FAMILY_POLICY_MISMATCH")
    digests = binding.get("digest_bindings", {})
    if digests.get("dataset_digest", {}).get("value") != RATIFIED_NORMALIZED_PANEL_DIGEST:
        reasons.append("DATASET_DIGEST_MISMATCH")
    constraints = envelope.get("system_constraints", {})
    if constraints.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if constraints.get("unchanged_retry_blocked") is not True:
        reasons.append("UNCHANGED_RETRY_BLOCK_VIOLATION")
    unique = tuple(dict.fromkeys(reasons))
    if unique:
        return BindingValidationVerdict.REJECTED_INCOMPLETE, unique
    return BindingValidationVerdict.ACCEPTED_COMPLETE, ()


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
        "manifest_owner": MANIFEST_OWNER,
        "materializer_owner": MATERIALIZER_OWNER,
        "validator_owner": VALIDATOR_OWNER,
        "config_owner": CONFIG_REL_PATH,
        "governance_owner": GOVERNANCE_REL_PATH,
        "score_owner": (
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0"
        ),
        "orchestrator_owner": ORCHESTRATOR_OWNER,
        "pit_panel_owner": "src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1",
        "parallel_owner_created": False,
    }


def build_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decision": "NARROW_ADAPTER",
        "decision_ladder": "REUSE_AS_IS -> NARROW_ADAPTER",
        "dataset_panel_owner": "src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1",
        "pit_universe_owner": "pit_futures_universe_manifest_v1",
        "orchestrator_owner": ORCHESTRATOR_OWNER,
        "cost_stack_owner": "backtest_cost_models_v0",
        "period_binding_owner": "pit_cross_sectional_research_chronological_holdout_v1",
        "prior_relative_strength_binding_reference_only": True,
        "prior_relative_strength_binding_not_reused_unchanged": True,
        "new_parallel_owner_created": False,
    }


def build_semantic_identity_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "semantic_identity.v0",
        "research_scope": envelope["research_scope"],
        "hypothesis_id": envelope["hypothesis_id"],
        "strategy_family": envelope["strategy_family"],
        "score_family_policy": envelope["score_family_policy"],
        "score_definition": envelope["score_definition"],
        "ranking_formula": envelope["ranking_policy_binding"]["ranking_formula"],
        "selection_mode": envelope["ranking_policy_binding"]["selection_mode"],
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
        "prior_relative_strength_binding_digest": PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST,
        "cryptographic_binding_identity_changed": (
            envelope["binding_digest"] != PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST
        ),
    }


def build_binding_identity_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "binding_identity.v0",
        "research_scope": envelope["research_scope"],
        "hypothesis_id": envelope["hypothesis_id"],
        "hypothesis_version": envelope["hypothesis_version"],
        "binding_digest": envelope["binding_digest"],
        "implementation_digest": envelope["implementation_digest"],
        "config_digest": envelope["config_digest"],
        "same_semantic_binding": False,
        "unchanged_retry_blocked": True,
    }


def build_registry_binding_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "registry_binding.v0",
        "registry_status": "RATIFIED",
        "research_scope": envelope["research_scope"],
        "strategy_id": envelope["strategy_id"],
        "strategy_version": envelope["strategy_version"],
        "config_path": CONFIG_REL_PATH,
        "binding_digest": envelope["binding_digest"],
        "overall_binding_status": "COMPLETE",
        "economic_evaluation_executed": False,
        "promotion_eligible": False,
        "runtime_rewire_admissible": False,
        "live_authorized": False,
    }


def build_ratification_record_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "ratification_record.v0",
        "ratification_status": "PASS_VERSIONED_HYPOTHESIS_BINDING_RATIFICATION_V0",
        "operator_go": CONFIRM_GO,
        "research_scope": envelope["research_scope"],
        "binding_digest": envelope["binding_digest"],
        "source_feasibility_bundle": str(SOURCE_FEASIBILITY_BUNDLE),
        "material_difference_proven": True,
        "same_semantic_binding": False,
        "unchanged_retry_blocked": True,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "next_recommended_scope": NEXT_RECOMMENDED_SCOPE,
        "next_operator_go": NEXT_OPERATOR_GO,
    }


def validate_prior_relative_strength_not_reused_unchanged_v0(
    envelope: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    binding_digest = envelope.get("binding_digest")
    if binding_digest == PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST:
        reasons.append("PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST_REUSED")
    material = envelope.get("material_difference_from_prior", {})
    if material.get("prior_binding_not_reused_unchanged") is not True:
        reasons.append("PRIOR_RELATIVE_STRENGTH_BINDING_REUSE_FLAG_FALSE")
    if material.get("same_semantic_binding") is not False:
        reasons.append("SAME_SEMANTIC_BINDING_NOT_FALSE")
    if (
        material.get("distinct_hypothesis") is not True
        and material.get("material_difference_proven") is not True
    ):
        reasons.append("MATERIAL_DIFFERENCE_NOT_PROVEN")
    if envelope.get("score_family_policy") == PRIOR_RELATIVE_STRENGTH_SCORE_FAMILY:
        reasons.append("PRIOR_RELATIVE_STRENGTH_SCORE_FAMILY_REUSED")
    return not reasons, tuple(dict.fromkeys(reasons))


def validate_stale_or_wrong_digest_rejected_v0(
    envelope: Mapping[str, Any],
    *,
    stale_data_digest: str | None = None,
    stale_binding_digest: str | None = None,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if stale_data_digest and envelope.get("data_digest") == stale_data_digest:
        reasons.append("STALE_DATA_DIGEST_ACCEPTED")
    if stale_binding_digest and envelope.get("binding_digest") == stale_binding_digest:
        reasons.append("STALE_BINDING_DIGEST_ACCEPTED")
    return not reasons, tuple(reasons)


def build_field_classification_v0() -> dict[str, Any]:
    return {
        "schema_version": "field_classification.v0",
        "semantic_strategy_fields": [
            "hypothesis_statement",
            "score_definition",
            "score_family_policy",
            "ranking_formula",
            "ranking_direction",
        ],
        "semantic_ranking_fields": [
            "selection_mode",
            "long_top1_means",
            "short_top1_means",
            "deterministic_tie_break",
        ],
        "semantic_eligibility_fields": [
            "missing_instrument_policy",
            "stale_instrument_policy",
            "insufficient_history_policy",
            "minimum_rankable_instrument_count",
        ],
        "semantic_cost_fields": ["fee_binding", "slippage_binding", "spread_binding"],
        "semantic_execution_fields": ["execution_model_binding"],
        "cryptographic_dataset_fields": ["dataset_digest", "data_digest"],
        "cryptographic_binding_fields": [
            "binding_digest",
            "config_digest",
            "implementation_digest",
        ],
        "supersession_fields": [
            "source_feasibility_bundle",
            "source_ratification_evidence_dir",
            "prior_relative_strength_binding_digest",
        ],
        "unclassified_changed_field_count": 0,
    }


def build_binding_source_inputs_v0() -> dict[str, Any]:
    return {
        "schema_version": "binding_source_inputs.v0",
        "source_ratification_evidence_dir": str(SOURCE_RATIFICATION_EVIDENCE_DIR),
        "source_feasibility_bundle": str(SOURCE_FEASIBILITY_BUNDLE),
        "dataset_id": PANEL_DATASET_ID,
        "dataset_digest": RATIFIED_NORMALIZED_PANEL_DIGEST,
        "universe_id": UNIVERSE_ID,
        "universe_digest": compute_universe_digest_v0(),
        "score_family_policy": SCORE_FAMILY_POLICY,
        "semantic_binding_identity": SCORE_FAMILY_POLICY,
        "prior_relative_strength_scope": PRIOR_RELATIVE_STRENGTH_SCOPE,
        "prior_relative_strength_binding_digest": PRIOR_RELATIVE_STRENGTH_BINDING_DIGEST,
    }


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
        "new_scope": RESEARCH_SCOPE,
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
        "cryptographic_dataset_identity_changed": (
            prior_envelope.get("data_digest") != new_envelope.get("data_digest")
        ),
        "cryptographic_distinctness_proven": (
            prior_envelope.get("binding_digest") != new_envelope.get("binding_digest")
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
            "score_definition",
            prior_envelope.get("parameter_binding", {}).get("score_formula_expression"),
            new_envelope.get("score_definition"),
        ),
        (
            "binding_digest",
            prior_envelope.get("binding_digest"),
            new_envelope.get("binding_digest"),
        ),
        (
            "ranking_formula",
            None,
            new_envelope.get("ranking_policy_binding", {}).get("ranking_formula"),
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
