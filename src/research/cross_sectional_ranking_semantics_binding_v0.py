"""Cross-sectional ranking semantics declarative binding schema (v0).

Pure offline schema materialization for ratified policy classes. Does not compute
scores, rank instruments, run backtests, or authorize runtime execution.
"""

from __future__ import annotations

from copy import deepcopy
from enum import Enum
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_RANKING_SEMANTICS_BINDING_V0=true"
SCHEMA_VERSION = "cross_sectional_ranking_semantics_binding.v0"
HYPOTHESIS_ID = "CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"

# Ratified policy class values (immutable for v0 materialization).
SCORE_FAMILY_POLICY = "volatility_normalized_fixed_lookback_return"
DIRECTION_POLICY = "symmetric_top1_sign"
NEGATIVE_TOP1_MEANS = "SHORT_TOP1"
BOTTOM1_SELECTION_ALLOWED = False
ZERO_SCORE_TARGET = "FLAT"
NON_FINITE_SCORE_TARGET = "FLAT"
WARMUP_INCOMPLETE_TARGET = "FLAT"
PANEL_INSUFFICIENT_TARGET = "FLAT"

SIGNAL_TIMING_POLICY = "finalized_bar_close_epoch"
MINIMUM_SIGNAL_LAG_BARS = 1
SAME_BAR_EXECUTION_ALLOWED = False

REBALANCE_POLICY_CLASS = "fixed_N_bar_cadence"

SWITCH_POLICY = "flat_then_wait_one_epoch_then_enter"
OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT = True
ATOMIC_SIDE_SWITCH_ALLOWED = False

COOLDOWN_POLICY = "no_cooldown"
MINIMUM_HOLD_POLICY = "until_next_rebalance"
RISK_AND_SAFETY_EXITS_OVERRIDE_MINIMUM_HOLD = True

PANEL_COMPLETENESS_POLICY = "per_instrument_eligibility_mask"
MINIMUM_ELIGIBLE_COUNT_REQUIRED = True

MISSING_BAR_POLICY = "exclude_non_selected_instrument_for_epoch"
SELECTED_INSTRUMENT_MISSING_ACTION = "FORCE_FLAT"
BAR_CARRY_FORWARD_ALLOWED = False

TIE_BREAK_POLICY = "score_desc_then_instrument_id_asc"
TIE_BREAK_SCORE_SOURCE = "unrounded_internal_score"

THRESHOLD_POLICY = "sign_boundary_only"
NUMERIC_STRENGTH_THRESHOLD_INITIAL = False

ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"
ORCHESTRATOR_SCOPE = "RESEARCH_ONLY"

NUMERIC_BINDING_KEYS = (
    "lookback_N",
    "vol_window_V",
    "vol_epsilon",
    "vol_return_method",
    "rebalance_interval_bars",
    "signal_lag_bars",
    "min_eligible_members_for_rank",
    "switch_entry_delay_epochs",
    "max_bar_staleness_bars",
    "min_abs_score_strength",
)

EXTERNAL_BINDING_KEYS = (
    "pit_universe_manifest_ref",
    "instrument_id_canonicalization_version",
    "panel_ohlcv_dataset_manifest_ref",
    "admissibility_manifest_ref",
    "evaluation_period_binding",
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
)


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


def materialize_cross_sectional_ranking_semantics_binding_v0() -> dict[str, Any]:
    """Materialize ratified policy classes with fail-closed unbound numeric/external fields."""
    numeric_bindings: dict[str, dict[str, Any]] = {
        key: _field(BindingFieldStatus.REQUIRED_UNBOUND) for key in NUMERIC_BINDING_KEYS
    }
    numeric_bindings["min_abs_score_strength"] = _field(BindingFieldStatus.NOT_APPLICABLE)

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
        },
        "direction_semantics": {
            "selection_mode": "single_top1_by_score_desc",
            "ascending_rank_for_short_selection_forbidden": True,
            "bottom1_selection_allowed": BOTTOM1_SELECTION_ALLOWED,
            "dual_rank_forbidden": True,
            "negative_top1_means": NEGATIVE_TOP1_MEANS,
            "positive_top1_means": "LONG_TOP1",
            "zero_score_target": ZERO_SCORE_TARGET,
            "non_finite_score_target": NON_FINITE_SCORE_TARGET,
            "warmup_incomplete_target": WARMUP_INCOMPLETE_TARGET,
            "panel_insufficient_target": PANEL_INSUFFICIENT_TARGET,
        },
        "timing_semantics": {
            "decision_input": "finalized_bars_only",
            "score_epoch": "finalized_bar_close",
            "minimum_signal_lag_bars": MINIMUM_SIGNAL_LAG_BARS,
            "same_bar_execution": SAME_BAR_EXECUTION_ALLOWED,
            "finalized_bar_required": True,
            "pit_universe_at_score_epoch": True,
            "immutable_score_ledger": True,
        },
        "switch_semantics": {
            "switch_policy": SWITCH_POLICY,
            "opposite_side_requires_reconciled_flat": OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT,
            "flat_then_wait_one_epoch_then_enter": True,
            "atomic_side_switch": ATOMIC_SIDE_SWITCH_ALLOWED,
        },
        "missing_bar_semantics": {
            "missing_bar_policy": MISSING_BAR_POLICY,
            "non_selected_missing": "exclude_for_epoch",
            "selected_missing": SELECTED_INSTRUMENT_MISSING_ACTION.lower(),
            "carry_forward": BAR_CARRY_FORWARD_ALLOWED,
        },
        "panel_semantics": {
            "eligibility_mode": PANEL_COMPLETENESS_POLICY,
            "minimum_eligible_member_count_required": MINIMUM_ELIGIBLE_COUNT_REQUIRED,
            "insufficient_panel_action": "flat",
        },
        "minimum_hold_semantics": {
            "default_hold": MINIMUM_HOLD_POLICY,
            "risk_exit_override": RISK_AND_SAFETY_EXITS_OVERRIDE_MINIMUM_HOLD,
            "safety_exit_override": RISK_AND_SAFETY_EXITS_OVERRIDE_MINIMUM_HOLD,
        },
        "tie_break_semantics": {
            "primary_order": "score_desc",
            "secondary_order": "instrument_id_asc",
            "score_representation": TIE_BREAK_SCORE_SOURCE,
            "tie_break_policy": TIE_BREAK_POLICY,
        },
        "threshold_semantics": {
            "threshold_policy": THRESHOLD_POLICY,
            "numeric_strength_threshold_initial": NUMERIC_STRENGTH_THRESHOLD_INITIAL,
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


def clone_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(binding))
