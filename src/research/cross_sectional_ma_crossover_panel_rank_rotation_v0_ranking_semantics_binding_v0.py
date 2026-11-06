"""MA-crossover panel rank-rotation cross-sectional ranking semantics binding schema (v0)."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from enum import Enum
from typing import Any, Mapping

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RANKING_SEMANTICS_BINDING_V0=true"
)
SCHEMA_VERSION = "cross_sectional_ma_crossover_panel_rank_rotation_v0_ranking_semantics_binding.v0"
HYPOTHESIS_ID = "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_NON_BITCOIN_PERPETUALS_V0"

SCORE_FAMILY_POLICY = "canonical_ma_crossover_normalized_spread_v0"
DIRECTION_POLICY = "symmetric_top1_sign_ma_crossover_score_v0"
SELECTION_MODE = "top1_by_ma_crossover_score_desc_single_slot_rotation_v0"
NEGATIVE_TOP1_MEANS = "SHORT_TOP1"
ZERO_SCORE_TARGET = "FLAT"
NON_FINITE_SCORE_TARGET = "FLAT"
WARMUP_INCOMPLETE_TARGET = "FLAT"
PANEL_INSUFFICIENT_TARGET = "FLAT"

SIGNAL_TIMING_POLICY = "finalized_bar_close_epoch"
MINIMUM_SIGNAL_LAG_BARS = 1
SAME_BAR_EXECUTION_ALLOWED = False
REBALANCE_POLICY_CLASS = "fixed_N_bar_cadence"
SWITCH_POLICY = "flat_then_wait_one_epoch_then_enter"
COOLDOWN_POLICY = "no_cooldown"
MINIMUM_HOLD_POLICY = "until_next_rebalance"
PANEL_COMPLETENESS_POLICY = "per_instrument_eligibility_mask"
MISSING_BAR_POLICY = "exclude_non_selected_instrument_for_epoch"
TIE_BREAK_POLICY = "score_desc_then_instrument_id_asc"
THRESHOLD_POLICY = "sign_boundary_only"

ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"
ORCHESTRATOR_SCOPE = "RESEARCH_ONLY"

NUMERIC_BINDING_KEYS = (
    "fast_window",
    "slow_window",
    "rebalance_interval_bars",
    "signal_lag_bars",
    "min_eligible_members_for_rank",
    "switch_entry_delay_epochs",
    "max_bar_staleness_bars",
    "max_active_instruments",
    "entry_rank_threshold",
    "hold_exit_rank_threshold",
)

EXTERNAL_BINDING_KEYS = (
    "pit_universe_manifest_ref",
    "instrument_id_canonicalization_version",
    "panel_ohlcv_dataset_manifest_ref",
    "instruments_artifact_ref",
    "admissibility_manifest_ref",
    "evaluation_period_binding",
    "source_closeout_bundle_ref",
    "fee_model_version",
    "slippage_model_version",
    "funding_model_version",
    "spread_model_version",
    "execution_model_version",
)

DIGEST_BINDING_KEYS = (
    "implementation_digest",
    "config_digest",
    "data_digest",
    "material_difference_digest",
    "universe_instruments_digest",
)

VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_ranking_semantics_binding_v0.json"
)

RATIFIED_OPERATOR_BINDING_VALUES: dict[str, int | float | str] = {
    "fast_window": 20,
    "slow_window": 50,
    "rebalance_interval_bars": 1,
    "signal_lag_bars": 1,
    "min_eligible_members_for_rank": 5,
    "switch_entry_delay_epochs": 1,
    "max_bar_staleness_bars": 1,
    "max_active_instruments": 1,
    "entry_rank_threshold": 1,
    "hold_exit_rank_threshold": 1,
}

RATIFIED_OPERATOR_RATIONALES: dict[str, str] = {
    "fast_window": (
        "Reuses ratified ma_crossover/v1 fast_window=20 without mutation or optimization."
    ),
    "slow_window": (
        "Reuses ratified ma_crossover/v1 slow_window=50 without mutation or optimization."
    ),
    "rebalance_interval_bars": (
        "Cross-sectional ranking recomputed every finalized PT1H epoch; research-only."
    ),
    "signal_lag_bars": ("One full bar lag prevents look-ahead on SMA inputs at score epoch."),
    "min_eligible_members_for_rank": (
        "Fail-closed minimum of five simultaneously eligible panel members."
    ),
    "switch_entry_delay_epochs": (
        "After selection change wait one finalized epoch before entry per switch policy."
    ),
    "max_bar_staleness_bars": (
        "At most one bar staleness tolerance; older members excluded from ranking."
    ),
    "max_active_instruments": (
        "Single-slot top-1 rotation geometry per scope ratification; not a portfolio basket."
    ),
    "entry_rank_threshold": (
        "Only rank-1 instrument is eligible for active slot entry; no threshold rescue."
    ),
    "hold_exit_rank_threshold": (
        "Active slot exits when instrument is no longer rank-1 at rebalance epoch."
    ),
}


def compute_operator_decision_digest_v0(
    operator_values: Mapping[str, int | float | str] | None = None,
    operator_rationales: Mapping[str, str] | None = None,
) -> str:
    values = dict(operator_values or RATIFIED_OPERATOR_BINDING_VALUES)
    rationales = dict(operator_rationales or RATIFIED_OPERATOR_RATIONALES)
    digest_input = {
        key: {"value": values[key], "rationale": rationales[key]} for key in sorted(values)
    }
    canonical = json.dumps(
        digest_input,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


ATTESTED_OPERATOR_DECISION_DIGEST = compute_operator_decision_digest_v0()


class BindingFieldStatus(str, Enum):
    REQUIRED_UNBOUND = "REQUIRED_UNBOUND"
    BOUND = "BOUND"
    INVALID = "INVALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AggregateBindingStatus(str, Enum):
    BOUND = "BOUND"
    REQUIRED_UNBOUND = "REQUIRED_UNBOUND"
    INCOMPLETE_FAIL_CLOSED = "INCOMPLETE_FAIL_CLOSED"
    COMPLETE = "COMPLETE"


def _field(
    status: BindingFieldStatus,
    *,
    value: Any = None,
    ref: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": status.value}
    if value is not None:
        payload["value"] = value
    if ref:
        payload["ref"] = ref
    return payload


def materialize_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0() -> dict[str, Any]:
    numeric_bindings = {
        key: _field(BindingFieldStatus.REQUIRED_UNBOUND) for key in NUMERIC_BINDING_KEYS
    }
    external_bindings = {
        key: _field(BindingFieldStatus.REQUIRED_UNBOUND) for key in EXTERNAL_BINDING_KEYS
    }
    digest_bindings = {
        key: _field(BindingFieldStatus.REQUIRED_UNBOUND) for key in DIGEST_BINDING_KEYS
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis_id": HYPOTHESIS_ID,
        "policy_classes": {
            "score_family_policy": SCORE_FAMILY_POLICY,
            "direction_policy": DIRECTION_POLICY,
            "signal_timing_policy": SIGNAL_TIMING_POLICY,
            "rebalance_policy_class": REBALANCE_POLICY_CLASS,
            "switch_policy": SWITCH_POLICY,
            "cooldown_policy": COOLDOWN_POLICY,
            "minimum_hold_policy": MINIMUM_HOLD_POLICY,
            "panel_completeness_policy": PANEL_COMPLETENESS_POLICY,
            "missing_bar_policy": MISSING_BAR_POLICY,
            "tie_break_policy": TIE_BREAK_POLICY,
            "threshold_policy": THRESHOLD_POLICY,
        },
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
            "signal_logic_change_allowed": False,
            "parameter_optimization_allowed": False,
            "post_result_threshold_change_forbidden": True,
            "post_result_policy_change_forbidden": True,
        },
        "direction_semantics": {
            "selection_mode": SELECTION_MODE,
            "negative_top1_means": NEGATIVE_TOP1_MEANS,
            "zero_score_target": ZERO_SCORE_TARGET,
            "non_finite_score_target": NON_FINITE_SCORE_TARGET,
            "warmup_incomplete_target": WARMUP_INCOMPLETE_TARGET,
            "panel_insufficient_target": PANEL_INSUFFICIENT_TARGET,
            "single_slot_rotation": True,
            "rotation_requires_reconciled_flat": True,
            "underlying_signal_binding": "ma_crossover/v1",
        },
        "timing_semantics": {
            "decision_input": "finalized_bars_only",
            "score_epoch": "finalized_bar_close",
            "minimum_signal_lag_bars": MINIMUM_SIGNAL_LAG_BARS,
            "same_bar_execution": SAME_BAR_EXECUTION_ALLOWED,
            "finalized_bar_required": True,
            "pit_universe_at_score_epoch": True,
            "price_col": "close",
        },
        "switch_semantics": {
            "switch_policy": SWITCH_POLICY,
            "opposite_side_requires_reconciled_flat": True,
            "flat_then_wait_one_epoch_then_enter": True,
            "atomic_side_switch": False,
        },
        "missing_bar_semantics": {
            "missing_bar_policy": MISSING_BAR_POLICY,
            "non_selected_missing": "exclude_for_epoch",
            "selected_missing": "force_flat",
            "carry_forward": False,
            "stale_instrument_action": "exclude_at_score_epoch",
        },
        "panel_semantics": {
            "eligibility_mode": PANEL_COMPLETENESS_POLICY,
            "minimum_eligible_member_count_required": True,
            "insufficient_panel_action": "flat",
            "survivorship_handling": "pit_lifecycle_registry_bound_fail_closed",
        },
        "portfolio_semantics": {
            "weighting_policy": "single_slot_full_notional_on_selected_instrument",
            "gross_exposure_cap": 1.0,
            "net_exposure_range": (-1.0, 1.0),
            "turnover_accounting": "per_rotation_event_and_side_change",
            "trade_count_accounting": "entry_exit_and_rotation_events",
        },
        "tie_break_semantics": {
            "tie_break_policy": TIE_BREAK_POLICY,
            "tie_break_score_source": "unrounded_internal_score",
        },
        "threshold_semantics": {
            "threshold_policy": THRESHOLD_POLICY,
            "numeric_strength_threshold_initial": False,
            "entry_rank_threshold_required": True,
            "hold_exit_rank_threshold_required": True,
        },
        "orchestrator": {
            "owner": ORCHESTRATOR_OWNER,
            "scope": ORCHESTRATOR_SCOPE,
        },
        "numeric_bindings": numeric_bindings,
        "external_bindings": external_bindings,
        "digest_bindings": digest_bindings,
        "binding_status": {
            "policy_classes_status": AggregateBindingStatus.BOUND.value,
            "numeric_bindings_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "universe_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "dataset_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "period_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "cost_model_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "digest_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "overall_binding_status": AggregateBindingStatus.INCOMPLETE_FAIL_CLOSED.value,
        },
    }


def compute_config_digest_v0(config_bytes: bytes) -> str:
    return hashlib.sha256(config_bytes).hexdigest()


def apply_ratified_operator_bindings_v0(binding: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(binding)
    numeric = result["numeric_bindings"]
    for key, value in RATIFIED_OPERATOR_BINDING_VALUES.items():
        numeric[key] = _field(BindingFieldStatus.BOUND, value=value)
    status = result["binding_status"]
    status["numeric_bindings_status"] = AggregateBindingStatus.BOUND.value
    status["overall_binding_status"] = AggregateBindingStatus.INCOMPLETE_FAIL_CLOSED.value
    return result


def materialize_versioned_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0() -> dict[
    str, Any
]:
    binding = apply_ratified_operator_bindings_v0(
        materialize_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0()
    )
    return {
        "artifact_kind": (
            "cross_sectional_ma_crossover_panel_rank_rotation_ranking_semantics_versioned_binding"
        ),
        "artifact_version": "v0",
        "binding": binding,
        "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
    }


def serialize_versioned_binding_artifact_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(dict(envelope), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
