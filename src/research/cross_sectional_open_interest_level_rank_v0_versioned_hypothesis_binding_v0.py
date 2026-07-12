"""Versioned hypothesis binding for cross_sectional_open_interest_level_rank/v0.

Binds the ratified five-instrument self-accumulated open-interest panel for a distinct
point-in-time OI level ranking hypothesis. Research-only; no runtime or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_open_interest_level_rank_scoring_v0 import (
    OPEN_INTEREST_SIGNAL_LAG,
    SCORE_FORMULA_EXPRESSION,
    SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_open_interest_level_rank_v0_pit_semantics_contract_v0 import (
    BAR_INTERVAL,
    CONTRACT_VERSION,
    OPEN_INTEREST_LEVEL_DEFINITION,
    RESEARCH_SCOPE,
    build_pit_open_interest_level_semantics_contract_v0,
    pit_semantics_contract_to_dict,
)
from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)
from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (
    DATASET_EXTENSION,
    DATASET_ID,
    MODULE_VERSION as MATERIALIZER_MODULE_VERSION,
    PANEL_DATASET_SCHEMA,
    PANEL_ID,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (
    REQUIRED_CONTIGUOUS_BARS,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING_V0=true"
BINDING_ARTIFACT_VERSION = "v0"
BINDING_SCHEMA_VERSION = (
    "cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding.v0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING_V0.md"
)
CONFIRM_GO = (
    "GO_CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING_IMPLEMENTATION_V0"
)

STRATEGY_ID = "cross_sectional_open_interest_level_rank"
STRATEGY_VERSION = "v0"
HYPOTHESIS_CLASS = "CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK"
RESEARCH_HYPOTHESIS_ID = "cross_sectional_open_interest_level_rank_v0"

PANEL_OI_MANIFEST_REF = (
    f"pit_okx_pt1h_panel_open_interest_dataset_v1:{PANEL_ID}:{DATASET_EXTENSION}"
)
PIT_UNIVERSE_MANIFEST_REF = (
    "pit_futures_universe_manifest_v1:"
    "pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1"
)
UNIVERSE_LIFECYCLE_REGISTRY_REF = "pit_futures_lifecycle_registry_v1:okx_production_lifecycle_v1"
ADMISSIBILITY_MANIFEST_REF = (
    f"pit_cross_sectional_research_dataset_envelope.v0:{DATASET_ID}:{DATASET_EXTENSION}"
)

RATIFIED_PANEL_DATASET_DIGEST = "37e492d6b2ef64ab681ca96ef5f2fc873d2d4f87c119b3ee2666d8489fc650a1"
RATIFIED_INSTRUMENT_UNIVERSE_DIGEST = (
    "e286db0053596e771c2168e82ff61c326f7ba1d51e90d606880237576b2c4791"
)
RATIFIED_BOUND_DATA_DIGEST = "82e8787c0cc19c15c120de4ee24821bba85b5c5a938b802cfa3f7bcd40f13a4d"
RATIFIED_ARCHIVE_SOURCE_DIGEST = "cb10e99d7cd5fa158a38aec24e095dbd051f447a0665a7fce47bcc13cb44860a"
OBSERVED_PANEL_WINDOW_START_UTC = "2026-07-09T12:00:00Z"
OBSERVED_PANEL_WINDOW_END_UTC = "2026-07-11T23:00:00Z"
OBSERVED_PANEL_HISTORY_DEPTH = 60

PRIOR_SCOPE = "cross_sectional_open_interest_delta_rank/v0"
PRIOR_HYPOTHESIS_ID = "cross_sectional_open_interest_delta_rank_v0"
PRIOR_BINDING_DIGEST = "49e444fddf31c2da877e2c30eb0135848a657d58febfbb1827affcb6154dfb64"
PRIOR_FEATURE = "delta_or_change_in_open_interest"
NEW_FEATURE = "point_in_time_open_interest_level"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
PRIOR_TERMINAL_BASELINE_REF = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_terminal_inconclusive_baseline_"
    "evidence_and_unchanged_retry_block_v0_20260712T011717Z"
)
SUPERSEDING_INTEGRITY_ATTESTATION_REF = (
    "config/research/"
    "cross_sectional_open_interest_delta_rank_v0_terminal_baseline_bundle_"
    "superseding_integrity_attestation_v0.json"
)
PROVISIONAL_RANK_SOURCE_REF = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_delta_rank_v0_post_terminal_evidence_"
    "distinct_hypothesis_ranking_read_only_v0_20260712T032121Z"
)

SELECTION_MODE = "open_interest_level_extremes_single_leg_rotation_v0"
RANKING_FORMULA = "rank_by_lagged_point_in_time_open_interest_level_v0"
RANKING_DIRECTION = "long_min_level_short_max_level_single_slot_rotation_v0"
DETERMINISTIC_TIE_BREAK = "instrument_id_asc_stable_sort"
MINIMUM_RANKABLE_INSTRUMENT_COUNT = len(CANONICAL_UNIVERSE_BINDING)
SELECTION_COUNT = 1
REBALANCE_CADENCE = "PT1H_every_finalized_bar_epoch"
WEIGHTING_POLICY = "equal_weight_single_slot_v0"
GROSS_EXPOSURE_POLICY = "unit_notional_single_slot_v0"
NET_EXPOSURE_POLICY = "directional_single_slot_v0"
PER_INSTRUMENT_CAP = 1.0
PORTFOLIO_CAP = 1.0

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

PANEL_CALENDAR_START_UTC = "2024-05-01T00:00:00Z"
PANEL_CALENDAR_END_UTC = "2024-09-01T00:00:00Z"
PANEL_WARMUP_BARS = OPEN_INTEREST_SIGNAL_LAG + 1
PERIOD_BINDING_ID = "pit_cross_sectional_research_chronological_holdout_v1"
PERIOD_BINDING_REF = f"pit_futures_cross_sectional_research_period_split_v1:{PERIOD_BINDING_ID}"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

NEXT_RECOMMENDED_SCOPE = (
    "CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
NEXT_OPERATOR_GO = (
    "GO_CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)

MANIFEST_OWNER = "scripts.ops.primary_evidence_retention_v0"
MATERIALIZER_OWNER = (
    "scripts.research."
    "materialize_cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0"
)
VALIDATOR_OWNER = (
    "src.research.cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0"
)

REQUIRED_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "preflight.txt",
    "source_manifest_verification.txt",
    "owner_inventory.json",
    "reuse_decision.json",
    "hypothesis_contract.json",
    "prior_hypothesis_comparison.json",
    "material_difference_proof.json",
    "dataset_binding.json",
    "universe_binding.json",
    "ranking_policy_binding.json",
    "selection_hold_exit_rotation_binding.json",
    "cost_and_execution_binding.json",
    "economic_and_robustness_contract.json",
    "field_classification.json",
    "digest_contracts.json",
    "digest_dependency_graph.json",
    "before_after_field_diff.json",
    "semantic_identity_comparison.json",
    "cryptographic_identity_comparison.json",
    "materializer_roundtrip.txt",
    "deterministic_materialization.txt",
    "runner_decision.json",
    "test_assertion_matrix.json",
    "test_results.txt",
    "changed_files.txt",
    "final_report.txt",
    "MANIFEST.sha256",
    "MANIFEST_VERIFY.log",
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


def _parse_utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0",
            "materializer_owner": MATERIALIZER_MODULE_VERSION,
            "pit_semantics_contract_version": CONTRACT_VERSION,
            "schema_version": BINDING_SCHEMA_VERSION,
            "selection_mode": SELECTION_MODE,
            "score_formula_version": SCORE_FORMULA_VERSION,
        }
    )


def compute_material_difference_digest_v0() -> str:
    return _stable_digest(
        {
            "prior_scope": PRIOR_SCOPE,
            "prior_feature": PRIOR_FEATURE,
            "new_feature": NEW_FEATURE,
            "distinct_hypothesis": True,
            "unchanged_retry": False,
            "open_interest_level_rank_signal": True,
            "open_interest_delta_rank_forbidden": True,
            "self_accumulated_panel_only": True,
            "no_399_instrument_fallback": True,
        }
    )


def build_hypothesis_statement_v0() -> str:
    return (
        "Cross-sectional positioning crowding hypothesis: rank instruments by point-in-time "
        "open-interest level at a lagged finalized bar; rotate a single slot toward low-OI "
        "(long) versus high-OI (short) extremes as a stock-based positioning hypothesis "
        "distinct from OI delta flow."
    )


def build_material_difference_from_prior_v0() -> dict[str, Any]:
    return {
        "prior_scope": PRIOR_SCOPE,
        "prior_hypothesis_id": PRIOR_HYPOTHESIS_ID,
        "prior_feature": PRIOR_FEATURE,
        "new_feature": NEW_FEATURE,
        "distinct_hypothesis": True,
        "unchanged_retry": False,
        "prior_ranking_input": "open_interest_delta_over_lookback_k",
        "new_ranking_input": "point_in_time_open_interest_level_at_signal_lag",
        "prior_economic_mechanism": "positioning_change_extremes",
        "new_economic_mechanism": "positioning_crowding_level_extremes",
        "prior_selection_mode": "open_interest_delta_rank_extremes_single_leg_rotation_v0",
        "new_selection_mode": SELECTION_MODE,
        "prior_binding_digest": PRIOR_BINDING_DIGEST,
        "prior_binding_not_reused_unchanged": True,
    }


def build_parameter_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "signal_lag_bars": OPEN_INTEREST_SIGNAL_LAG,
        "minimum_panel_bars": REQUIRED_CONTIGUOUS_BARS,
        "open_interest_observation_field": "open_interest",
        "open_interest_level_definition": OPEN_INTEREST_LEVEL_DEFINITION,
        "score_formula_version": SCORE_FORMULA_VERSION,
        "score_formula_expression": SCORE_FORMULA_EXPRESSION,
        "parameter_search_forbidden": True,
        "no_instrument_substitution": True,
        "no_universe_expansion": True,
        "unchanged_retry_of_failed_bindings_forbidden": True,
        "prior_delta_rank_binding_not_reused_unchanged": True,
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
        "universe_policy_id": (
            "pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe"
        ),
        "universe_policy_version": "v1",
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "universe_lifecycle_registry_ref": UNIVERSE_LIFECYCLE_REGISTRY_REF,
        "minimum_eligible_member_count": len(CANONICAL_UNIVERSE_BINDING),
        "maximum_eligible_member_count": len(CANONICAL_UNIVERSE_BINDING),
        "instrument_identity_normalization": INSTRUMENT_ID_CANONICALIZATION_VERSION,
        "target_instrument_bindings": [
            {"instrument_id": inst_id, "native_instrument_id": native_id}
            for inst_id, native_id in CANONICAL_UNIVERSE_BINDING
        ],
        "instrument_universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
    }


def build_dataset_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "dataset_id": DATASET_ID,
        "dataset_extension": DATASET_EXTENSION,
        "panel_id": PANEL_ID,
        "panel_dataset_schema": PANEL_DATASET_SCHEMA,
        "panel_open_interest_manifest_ref": PANEL_OI_MANIFEST_REF,
        "admissibility_manifest_ref": ADMISSIBILITY_MANIFEST_REF,
        "source_mode": "SELF_ACCUMULATED_EFFECTIVE_ARCHIVE_VIEW",
        "materializer_owner": MATERIALIZER_MODULE_VERSION,
        "no_fallback_to_399_instrument_dataset": True,
        "panel_dataset_digest": RATIFIED_PANEL_DATASET_DIGEST,
        "bound_data_digest": RATIFIED_BOUND_DATA_DIGEST,
        "archive_source_digest": RATIFIED_ARCHIVE_SOURCE_DIGEST,
        "observed_panel_window_start_utc": OBSERVED_PANEL_WINDOW_START_UTC,
        "observed_panel_window_end_utc": OBSERVED_PANEL_WINDOW_END_UTC,
        "observed_panel_history_depth": OBSERVED_PANEL_HISTORY_DEPTH,
        "bar_interval": BAR_INTERVAL,
    }


def build_ranking_policy_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "ranking_formula": RANKING_FORMULA,
        "ranking_direction": RANKING_DIRECTION,
        "deterministic_tie_break": DETERMINISTIC_TIE_BREAK,
        "minimum_rankable_instrument_count": MINIMUM_RANKABLE_INSTRUMENT_COUNT,
        "missing_instrument_policy": "explicit_none_fail_closed_no_zero_fallback",
        "stale_instrument_policy": "exclude_when_staleness_exceeds_threshold_bars",
        "invalid_observation_policy": "exclude_non_finite_force_flat_at_selection",
        "selection_mode": SELECTION_MODE,
        "long_leg_means": "LONG_MIN_LEVEL",
        "short_leg_means": "SHORT_MAX_LEVEL",
        "finalized_bar_only": True,
        "point_in_time_semantics": OPEN_INTEREST_LEVEL_DEFINITION,
    }


def build_selection_hold_exit_rotation_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "selection_count": SELECTION_COUNT,
        "long_selection_semantics": "single_slot_long_min_open_interest_level_v0",
        "short_selection_semantics": "single_slot_short_max_open_interest_level_v0",
        "simultaneous_long_short_policy": "forbidden_single_slot_rotation_only",
        "rebalance_cadence": REBALANCE_CADENCE,
        "rebalance_interval_bars": 1,
        "hold_semantics": "until_next_rebalance",
        "exit_semantics": "rotation_via_switch_policy_flat_then_wait_one_epoch",
        "rotation_semantics": "single_slot_extreme_level_rotation_v0",
        "turnover_control_semantics": "switch_entry_delay_one_epoch_no_cooldown",
        "switch_entry_delay_epochs": 1,
        "weighting_policy": WEIGHTING_POLICY,
        "gross_exposure_policy": GROSS_EXPOSURE_POLICY,
        "net_exposure_policy": NET_EXPOSURE_POLICY,
        "per_instrument_cap": PER_INSTRUMENT_CAP,
        "portfolio_cap": PORTFOLIO_CAP,
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
            "minimum_trade_count": 50,
        },
        "sample_sufficiency_contract": {
            "minimum_panel_history_depth": OBSERVED_PANEL_HISTORY_DEPTH,
            "minimum_rankable_epoch_count": OBSERVED_PANEL_HISTORY_DEPTH - OPEN_INTEREST_SIGNAL_LAG,
            "minimum_trade_count": 50,
            "sample_sufficiency_evaluated_in_binding_scope": False,
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
        "failure_taxonomy": {
            "binding_incomplete": "REJECTED_INCOMPLETE",
            "stale_digest": "STALE_DIGEST_REJECTED",
            "prior_binding_reuse": "PRIOR_DELTA_RANK_BINDING_REUSE_REJECTED",
            "insufficient_panel": "PANEL_INSUFFICIENT_FLAT",
            "non_finite_observation": "NON_FINITE_FORCE_FLAT",
        },
        "unchanged_retry_policy": {
            "unchanged_retry_blocked": True,
            "prior_inconclusive_baseline_unchanged_retry_forbidden": True,
            "prior_binding_digest_unchanged_retry_forbidden": True,
        },
    }


def build_period_binding_v0() -> dict[str, Any]:
    start = _parse_utc(PANEL_CALENDAR_START_UTC)
    end = _parse_utc(PANEL_CALENDAR_END_UTC)
    total_bars = int((end - start).total_seconds() // 3600)
    warmup_end = start + timedelta(hours=PANEL_WARMUP_BARS - 1)
    post_warmup_bars = total_bars - PANEL_WARMUP_BARS
    training_bars = int(post_warmup_bars * 0.40)
    validation_bars = int(post_warmup_bars * 0.30)
    training_start = warmup_end + timedelta(hours=1)
    training_end = training_start + timedelta(hours=training_bars - 1)
    validation_start = training_end + timedelta(hours=3)
    validation_end = validation_start + timedelta(hours=validation_bars - 1)
    oos_start = validation_end + timedelta(hours=3)
    oos_end = end - timedelta(hours=1)
    return {
        "binding_version": "v1",
        "period_binding_id": PERIOD_BINDING_ID,
        "split_policy_id": PERIOD_BINDING_ID,
        "split_timezone": "UTC",
        "boundary_semantics": "utc_bar_close_inclusive_end",
        "warmup_start": _format_utc(start),
        "warmup_end": _format_utc(warmup_end),
        "training_start": _format_utc(training_start),
        "training_end": _format_utc(training_end),
        "validation_start": _format_utc(validation_start),
        "validation_end": _format_utc(validation_end),
        "out_of_sample_start": _format_utc(oos_start),
        "out_of_sample_end": _format_utc(oos_end),
        "embargo_duration": "PT2H",
        "purge_duration": "PT2H",
        "periods_frozen_before_evaluation": True,
        "no_overlap_enforced": True,
        "holdout_isolation_enforced": True,
    }


def build_runner_decision_v0() -> dict[str, Any]:
    return {
        "schema_version": "runner_decision.v0",
        "runner_required": True,
        "runner_action": "DEFER_TO_FUTURE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE",
        "canonical_entry_point": None,
        "canonical_entry_point_status": "UNKNOWN_BLOCKER_FOR_EVALUATION_SCOPE",
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
) -> dict[str, Any]:
    return {
        "schema_version": "digest_dependency_graph.v0",
        "self_reference_excluded": True,
        "edges": [
            {"from": "semantic_source_fields", "to": "component_digests"},
            {"from": "pit_semantics_contract.semantic_digest", "to": "implementation_digest"},
            {"from": "parameter_binding", "to": "config_digest"},
            {"from": "pit_universe_binding", "to": "config_digest"},
            {"from": "dataset_binding", "to": "config_digest"},
            {"from": "ranking_policy_binding", "to": "config_digest"},
            {"from": "selection_hold_exit_rotation_binding", "to": "config_digest"},
            {"from": "period_binding", "to": "config_digest"},
            {"from": "config_digest", "to": "binding_digest"},
            {"from": "data_digest", "to": "binding_digest"},
            {"from": "implementation_digest", "to": "binding_digest"},
            {"from": "material_difference_digest", "to": "binding_digest"},
        ],
        "component_digests": {
            "implementation_digest": implementation_digest,
            "config_digest": config_digest,
            "data_digest": RATIFIED_PANEL_DATASET_DIGEST,
            "material_difference_digest": material_difference_digest,
            "instrument_universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
            "universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
            "dataset_digest": RATIFIED_PANEL_DATASET_DIGEST,
            "binding_digest": binding_digest,
        },
    }


def materialize_versioned_hypothesis_binding_v0() -> dict[str, Any]:
    pit_contract = build_pit_open_interest_level_semantics_contract_v0()
    parameter_binding = build_parameter_binding_v0()
    pit_universe_binding = build_pit_universe_binding_v0()
    dataset_binding = build_dataset_binding_v0()
    ranking_policy_binding = build_ranking_policy_binding_v0()
    selection_binding = build_selection_hold_exit_rotation_binding_v0()
    period_binding = build_period_binding_v0()
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
        }
    )
    implementation_digest = compute_implementation_digest_v0()
    material_difference_digest = compute_material_difference_digest_v0()
    binding_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "data_digest": RATIFIED_PANEL_DATASET_DIGEST,
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
            "data_digest": _field_bound(value=RATIFIED_PANEL_DATASET_DIGEST),
            "dataset_digest": _field_bound(value=RATIFIED_PANEL_DATASET_DIGEST),
            "universe_digest": _field_bound(value=RATIFIED_INSTRUMENT_UNIVERSE_DIGEST),
            "implementation_digest": _field_bound(value=implementation_digest),
            "material_difference_digest": _field_bound(value=material_difference_digest),
            "instrument_universe_digest": _field_bound(value=RATIFIED_INSTRUMENT_UNIVERSE_DIGEST),
            "bound_data_digest": _field_bound(value=RATIFIED_BOUND_DATA_DIGEST),
            "binding_digest": _field_bound(value=binding_digest),
        },
        "direction_semantics": {
            "selection_mode": SELECTION_MODE,
            "long_leg_means": "LONG_MIN_LEVEL",
            "short_leg_means": "SHORT_MAX_LEVEL",
            "single_slot_rotation": True,
            "panel_insufficient_target": "FLAT",
            "warmup_incomplete_target": "FLAT",
            "non_finite_open_interest_target": "FLAT",
        },
        "external_bindings": {
            "pit_universe_manifest_ref": _field_bound(ref=PIT_UNIVERSE_MANIFEST_REF),
            "instrument_id_canonicalization_version": _field_bound(
                value=INSTRUMENT_ID_CANONICALIZATION_VERSION
            ),
            "panel_open_interest_dataset_manifest_ref": _field_bound(ref=PANEL_OI_MANIFEST_REF),
            "admissibility_manifest_ref": _field_bound(ref=ADMISSIBILITY_MANIFEST_REF),
            "pit_semantics_contract_version": _field_bound(value=CONTRACT_VERSION),
            "fee_model_version": _field_bound(value=FEE_MODEL_VERSION),
            "slippage_model_version": _field_bound(value=SLIPPAGE_MODEL_VERSION),
            "funding_model_version": _field_bound(value=FUNDING_MODEL_VERSION),
            "spread_model_version": _field_bound(value=SPREAD_MODEL_VERSION),
            "execution_model_version": _field_bound(value=EXECUTION_MODEL_VERSION),
            "evaluation_period_binding": _field_bound(ref=PERIOD_BINDING_REF),
            "prior_terminal_baseline_ref": _field_bound(ref=str(PRIOR_TERMINAL_BASELINE_REF)),
            "superseding_integrity_attestation_ref": _field_bound(
                ref=SUPERSEDING_INTEGRITY_ATTESTATION_REF
            ),
            "provisional_rank_source_ref": _field_bound(ref=str(PROVISIONAL_RANK_SOURCE_REF)),
        },
        "parameter_binding": parameter_binding,
        "pit_universe_binding": pit_universe_binding,
        "dataset_binding": dataset_binding,
        "ranking_policy_binding": ranking_policy_binding,
        "selection_hold_exit_rotation_binding": selection_binding,
        "period_binding": period_binding,
        "material_difference_from_prior": material_difference,
        "prior_hypothesis_lineage": {
            "prior_scope": PRIOR_SCOPE,
            "prior_hypothesis_id": PRIOR_HYPOTHESIS_ID,
            "prior_binding_digest": PRIOR_BINDING_DIGEST,
            "historical_evidence_preserved": True,
            "prior_inconclusive_economic_evidence_preserved": True,
            "unchanged_retry_blocked": True,
        },
    }

    return {
        "artifact_kind": (
            "cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding"
        ),
        "artifact_version": BINDING_ARTIFACT_VERSION,
        "schema_version": BINDING_SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_class": HYPOTHESIS_CLASS,
        "research_hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "research_scope": RESEARCH_SCOPE,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "hypothesis_version": STRATEGY_VERSION,
        "hypothesis_statement": build_hypothesis_statement_v0(),
        "material_difference_from_prior_open_interest_delta_rank_v0": material_difference,
        "prior_terminal_baseline_ref": str(PRIOR_TERMINAL_BASELINE_REF),
        "superseding_integrity_attestation_ref": SUPERSEDING_INTEGRITY_ATTESTATION_REF,
        "provisional_rank_source_ref": str(PROVISIONAL_RANK_SOURCE_REF),
        "signal_definition": SCORE_FORMULA_EXPRESSION,
        "open_interest_level_definition": OPEN_INTEREST_LEVEL_DEFINITION,
        "point_in_time_semantics": OPEN_INTEREST_LEVEL_DEFINITION,
        "finalized_bar_only": True,
        "bar_interval": BAR_INTERVAL,
        "instrument_universe": [inst_id for inst_id, _ in CANONICAL_UNIVERSE_BINDING],
        "instrument_universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
        "bitcoin_present": False,
        "futures_only": True,
        "ranking_formula": RANKING_FORMULA,
        "ranking_direction": RANKING_DIRECTION,
        "deterministic_tie_break": DETERMINISTIC_TIE_BREAK,
        "minimum_rankable_instrument_count": MINIMUM_RANKABLE_INSTRUMENT_COUNT,
        "missing_instrument_policy": ranking_policy_binding["missing_instrument_policy"],
        "stale_instrument_policy": ranking_policy_binding["stale_instrument_policy"],
        "invalid_observation_policy": ranking_policy_binding["invalid_observation_policy"],
        "selection_count": SELECTION_COUNT,
        "long_selection_semantics": selection_binding["long_selection_semantics"],
        "short_selection_semantics": selection_binding["short_selection_semantics"],
        "simultaneous_long_short_policy": selection_binding["simultaneous_long_short_policy"],
        "rebalance_cadence": REBALANCE_CADENCE,
        "hold_semantics": selection_binding["hold_semantics"],
        "exit_semantics": selection_binding["exit_semantics"],
        "rotation_semantics": selection_binding["rotation_semantics"],
        "turnover_control_semantics": selection_binding["turnover_control_semantics"],
        "weighting_policy": WEIGHTING_POLICY,
        "gross_exposure_policy": GROSS_EXPOSURE_POLICY,
        "net_exposure_policy": NET_EXPOSURE_POLICY,
        "per_instrument_cap": PER_INSTRUMENT_CAP,
        "portfolio_cap": PORTFOLIO_CAP,
        "cost_model_binding": cost_binding["cost_model_binding"],
        "fee_binding": cost_binding["fee_binding"],
        "slippage_binding": cost_binding["slippage_binding"],
        "funding_binding": cost_binding["funding_binding"],
        "spread_binding": cost_binding["spread_binding"],
        "execution_model_binding": cost_binding["execution_model_binding"],
        "economic_policy_binding": economic_robustness["economic_policy_binding"],
        "sample_sufficiency_contract": economic_robustness["sample_sufficiency_contract"],
        "walk_forward_contract": economic_robustness["walk_forward_contract"],
        "monte_carlo_contract": economic_robustness["monte_carlo_contract"],
        "stress_contract": economic_robustness["stress_contract"],
        "failure_taxonomy": economic_robustness["failure_taxonomy"],
        "unchanged_retry_policy": economic_robustness["unchanged_retry_policy"],
        "binding": binding,
        "pit_semantics_contract": pit_semantics_contract_to_dict(pit_contract),
        "parameter_binding": parameter_binding,
        "pit_universe_binding": pit_universe_binding,
        "panel_dataset_binding": dataset_binding,
        "ranking_policy_binding": ranking_policy_binding,
        "selection_hold_exit_rotation_binding": selection_binding,
        "period_binding": period_binding,
        "cost_execution_binding": cost_binding,
        "economic_and_robustness_contract": economic_robustness,
        "implementation_digest": implementation_digest,
        "config_digest": config_digest,
        "dataset_digest": RATIFIED_PANEL_DATASET_DIGEST,
        "universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
        "binding_digest": binding_digest,
        "binding_classification": "NEW_DISTINCT_HYPOTHESIS_MATERIAL_RANKING_INPUT_CHANGE",
        "semantic_binding_fields_changed": True,
        "cryptographic_binding_identity_changed": True,
        "runner_decision": build_runner_decision_v0(),
        "digest_dependency_graph": build_digest_dependency_graph_v0(
            config_digest=config_digest,
            implementation_digest=implementation_digest,
            material_difference_digest=material_difference_digest,
            binding_digest=binding_digest,
        ),
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "bitcoin_present": False,
            "spot_excluded": True,
            "synthetic_spot_excluded": True,
            "offline_only": True,
            "no_runtime": True,
            "no_parameter_optimization": True,
            "no_policy_rescue": True,
            "no_economic_evaluation": True,
            "no_universe_change": True,
            "prior_delta_rank_binding_not_reused_unchanged": True,
        },
        "data_digest": RATIFIED_PANEL_DATASET_DIGEST,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "economic_evaluation_executed": False,
    }


def validate_prior_delta_binding_not_reused_unchanged_v0(
    envelope: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if envelope.get("binding_digest") == PRIOR_BINDING_DIGEST:
        reasons.append("PRIOR_BINDING_DIGEST_REUSED")
    material = envelope.get("material_difference_from_prior_open_interest_delta_rank_v0", {})
    if material.get("prior_binding_not_reused_unchanged") is not True:
        reasons.append("PRIOR_BINDING_REUSE_FLAG_FALSE")
    if material.get("distinct_hypothesis") is not True:
        reasons.append("DISTINCT_HYPOTHESIS_FALSE")
    if envelope.get("binding", {}).get("parameter_binding", {}).get("rank_lookback_k") is not None:
        reasons.append("DELTA_RANK_LOOKBACK_K_PRESENT")
    selection_mode = (
        envelope.get("binding", {}).get("direction_semantics", {}).get("selection_mode")
    )
    if selection_mode == "open_interest_delta_rank_extremes_single_leg_rotation_v0":
        reasons.append("DELTA_RANK_SELECTION_MODE_REUSED")
    return not reasons, tuple(reasons)


def validate_versioned_hypothesis_binding_v0(
    envelope: Mapping[str, Any],
) -> tuple[BindingValidationVerdict, tuple[str, ...]]:
    reasons: list[str] = []
    binding = envelope.get("binding", {})
    status = binding.get("binding_status", {}).get("overall_binding_status")
    if status != "COMPLETE":
        reasons.append("BINDING_INCOMPLETE")

    digests = binding.get("digest_bindings", {})
    for key, expected in (
        ("data_digest", RATIFIED_PANEL_DATASET_DIGEST),
        ("instrument_universe_digest", RATIFIED_INSTRUMENT_UNIVERSE_DIGEST),
        ("bound_data_digest", RATIFIED_BOUND_DATA_DIGEST),
    ):
        entry = digests.get(key, {})
        if entry.get("value") != expected:
            reasons.append(f"DIGEST_MISMATCH:{key}")

    expected_binding_digest = envelope.get("binding_digest")
    bound_digest = digests.get("binding_digest", {}).get("value")
    if bound_digest != expected_binding_digest:
        reasons.append("BINDING_DIGEST_MISMATCH")

    constraints = envelope.get("system_constraints", {})
    if constraints.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if constraints.get("bitcoin_present") is not False:
        reasons.append("BITCOIN_PRESENT_VIOLATION")
    if constraints.get("prior_delta_rank_binding_not_reused_unchanged") is not True:
        reasons.append("PRIOR_DELTA_BINDING_REUSE_VIOLATION")

    ok_prior, prior_reasons = validate_prior_delta_binding_not_reused_unchanged_v0(envelope)
    if not ok_prior:
        reasons.extend(prior_reasons)

    dataset_binding = binding.get("dataset_binding", {})
    if dataset_binding.get("dataset_id") != DATASET_ID:
        reasons.append("DATASET_ID_MISMATCH")

    ranking = binding.get("ranking_policy_binding", {})
    if ranking.get("ranking_formula") != RANKING_FORMULA:
        reasons.append("RANKING_FORMULA_MISMATCH")
    if ranking.get("finalized_bar_only") is not True:
        reasons.append("FINALIZED_BAR_ONLY_VIOLATION")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return BindingValidationVerdict.REJECTED_INCOMPLETE, unique_reasons
    return BindingValidationVerdict.ACCEPTED_COMPLETE, ()


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


def load_versioned_hypothesis_binding_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return materialize_versioned_hypothesis_binding_v0()


def serialize_versioned_hypothesis_binding_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(envelope, indent=2, sort_keys=True) + "\n"


def materializer_to_binder_roundtrip_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    serialized = serialize_versioned_hypothesis_binding_json_v0(envelope)
    roundtrip = json.loads(serialized)
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
    diff_keys = sorted(set(first) ^ set(second))
    return False, {"diff_keys": diff_keys}


def build_owner_inventory() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v0",
        "manifest_owner": MANIFEST_OWNER,
        "materializer_owner": MATERIALIZER_OWNER,
        "validator_owner": VALIDATOR_OWNER,
        "config_owner": CONFIG_REL_PATH,
        "governance_owner": GOVERNANCE_REL_PATH,
        "pit_semantics_owner": (
            "src.research.cross_sectional_open_interest_level_rank_v0_pit_semantics_contract_v0"
        ),
        "scoring_owner": "src.research.cross_sectional_open_interest_level_rank_scoring_v0",
        "dataset_materializer_owner": MATERIALIZER_MODULE_VERSION,
        "parallel_manifest_owner_created": False,
        "parallel_digest_owner_created": False,
    }


def build_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "dataset_panel_owner": MATERIALIZER_MODULE_VERSION,
        "pit_universe_owner": "pit_futures_universe_manifest_v1",
        "cost_stack_owner": "backtest_cost_models_v0",
        "period_binding_owner": "pit_futures_cross_sectional_research_period_split_v1",
        "economic_policy_owner": "economic_validity_policy_v1",
        "prior_delta_rank_binding_reference_only": True,
        "prior_delta_rank_binding_not_reused_unchanged": True,
        "new_parallel_owner_created": False,
    }


def build_field_classification_v0() -> dict[str, Any]:
    return {
        "schema_version": "field_classification.v0",
        "semantic_strategy_fields": [
            "hypothesis_statement",
            "signal_definition",
            "open_interest_level_definition",
            "ranking_formula",
            "ranking_direction",
        ],
        "semantic_ranking_fields": [
            "selection_mode",
            "long_leg_means",
            "short_leg_means",
            "deterministic_tie_break",
        ],
        "semantic_eligibility_fields": [
            "missing_instrument_policy",
            "stale_instrument_policy",
            "invalid_observation_policy",
            "minimum_rankable_instrument_count",
        ],
        "semantic_cost_fields": ["fee_binding", "slippage_binding", "spread_binding"],
        "semantic_execution_fields": ["execution_model_binding"],
        "cryptographic_dataset_fields": ["dataset_digest", "data_digest", "bound_data_digest"],
        "cryptographic_binding_fields": [
            "binding_digest",
            "config_digest",
            "implementation_digest",
        ],
        "supersession_fields": [
            "prior_terminal_baseline_ref",
            "superseding_integrity_attestation_ref",
            "provisional_rank_source_ref",
        ],
        "unclassified_changed_field_count": 0,
    }


def build_before_after_field_diff_v0(
    *,
    prior_envelope: Mapping[str, Any],
    new_envelope: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    compare_keys = (
        "research_scope",
        "hypothesis_id",
        "ranking_formula",
        "ranking_direction",
        "selection_mode",
        "signal_definition",
        "open_interest_level_definition",
        "binding_digest",
    )
    for key in compare_keys:
        prior_val = prior_envelope.get(key)
        if key == "selection_mode":
            prior_val = (
                prior_envelope.get("binding", {})
                .get("direction_semantics", {})
                .get("selection_mode")
            )
            new_val = (
                new_envelope.get("binding", {}).get("direction_semantics", {}).get("selection_mode")
            )
        else:
            new_val = new_envelope.get(key)
        if prior_val != new_val:
            rows.append(
                {
                    "field": key,
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
        "prior_scope": PRIOR_SCOPE,
        "new_scope": RESEARCH_SCOPE,
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
        "cryptographic_dataset_identity_changed": False,
    }
