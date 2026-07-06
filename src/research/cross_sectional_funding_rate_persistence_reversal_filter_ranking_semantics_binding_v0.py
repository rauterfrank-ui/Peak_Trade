"""Funding-rate persistence reversal filter cross-sectional ranking semantics binding (v0)."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from enum import Enum
from typing import Any, Mapping

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_RANKING_SEMANTICS_BINDING_V0=true"
)
SCHEMA_VERSION = (
    "cross_sectional_funding_rate_persistence_reversal_filter_ranking_semantics_binding.v0"
)
HYPOTHESIS_ID = "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_NON_BITCOIN_PERPETUALS_V0"

SCORE_FAMILY_POLICY = "cross_sectional_funding_rate_persistence_reversal_filter_v0"
DIRECTION_POLICY = "symmetric_funding_persistence_decay_reversal_gate_single_leg_rotation_v0"
SELECTION_MODE = "funding_persistence_reversal_filter_extremes_single_leg_rotation_v0"
LONG_LEG_MEANS = "LONG_CROWDED_SHORT_REVERSAL"
SHORT_LEG_MEANS = "SHORT_CROWDED_LONG_REVERSAL"

SIGNAL_TIMING_POLICY = "finalized_bar_close_epoch"
MINIMUM_SIGNAL_LAG_BARS = 1
SAME_BAR_EXECUTION_ALLOWED = False
REBALANCE_POLICY_CLASS = "fixed_N_bar_cadence"
SWITCH_POLICY = "flat_then_wait_one_epoch_then_enter"
COOLDOWN_POLICY = "no_cooldown"
MINIMUM_HOLD_POLICY = "until_next_rebalance"
PANEL_COMPLETENESS_POLICY = "per_instrument_eligibility_mask"
MISSING_BAR_POLICY = "exclude_non_selected_instrument_for_epoch"
TIE_BREAK_POLICY = "combined_score_desc_then_instrument_id_asc"
THRESHOLD_POLICY = "persistence_combined_score_threshold_no_continuous_tuning"

ORCHESTRATOR_OWNER = (
    "cross_sectional_funding_rate_persistence_reversal_filter_single_slot_research_orchestrator_v0"
)
ORCHESTRATOR_SCOPE = "RESEARCH_ONLY"

NUMERIC_BINDING_KEYS = (
    "persistence_lookback_k",
    "min_persistence_epochs",
    "decay_stability_min_ratio",
    "reversal_risk_lookback_k",
    "adverse_reversal_threshold",
    "min_persistence_score_for_entry",
    "rebalance_interval_bars",
    "signal_lag_bars",
    "min_eligible_members_for_rank",
    "switch_entry_delay_epochs",
    "max_bar_staleness_bars",
)

EXTERNAL_BINDING_KEYS = (
    "pit_universe_manifest_ref",
    "instrument_id_canonicalization_version",
    "panel_funding_dataset_manifest_ref",
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
    "material_difference_digest",
)

VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_funding_rate_persistence_reversal_filter_v0_ranking_semantics_binding_v0.json"
)

RATIFIED_OPERATOR_BINDING_VALUES: dict[str, int | float | str] = {
    "persistence_lookback_k": 4,
    "min_persistence_epochs": 3,
    "decay_stability_min_ratio": 0.6,
    "reversal_risk_lookback_k": 2,
    "adverse_reversal_threshold": 0.00005,
    "min_persistence_score_for_entry": 0.5,
    "rebalance_interval_bars": 1,
    "signal_lag_bars": 1,
    "min_eligible_members_for_rank": 5,
    "switch_entry_delay_epochs": 1,
    "max_bar_staleness_bars": 1,
}

RATIFIED_OPERATOR_RATIONALES: dict[str, str] = {
    "persistence_lookback_k": ("Frozen K=4 PT1H bars for persistence window; no post-hoc tuning."),
    "min_persistence_epochs": (
        "At least three consecutive same-sign funding epochs required for entry."
    ),
    "decay_stability_min_ratio": ("Minimum decay stability ratio 0.6; frozen operator binding."),
    "reversal_risk_lookback_k": ("Two-bar reversal-risk lookback for adverse sign-flip gate."),
    "adverse_reversal_threshold": (
        "Frozen adverse reversal delta threshold 0.00005; no weakening."
    ),
    "min_persistence_score_for_entry": (
        "Combined persistence*decay score must be >= 0.5 for entry."
    ),
    "rebalance_interval_bars": (
        "Ranking recomputed every finalized epoch; research-only, no runtime effect."
    ),
    "signal_lag_bars": ("One full bar lag prevents look-ahead on funding observations."),
    "min_eligible_members_for_rank": (
        "At least five simultaneously eligible panel members for cross-sectional ranking."
    ),
    "switch_entry_delay_epochs": (
        "After leg change wait one epoch before entry per switch policy."
    ),
    "max_bar_staleness_bars": ("At most one bar staleness tolerance; older members excluded."),
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


def materialize_funding_persistence_reversal_filter_ranking_semantics_binding_v0() -> dict[
    str, Any
]:
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
        },
        "direction_semantics": {
            "selection_mode": SELECTION_MODE,
            "long_leg_means": LONG_LEG_MEANS,
            "short_leg_means": SHORT_LEG_MEANS,
            "dual_leg_simultaneous_forbidden": True,
            "single_slot_rotation": True,
            "funding_level_spread_forbidden": True,
            "rank_delta_forbidden": True,
            "panel_insufficient_target": "FLAT",
            "warmup_incomplete_target": "FLAT",
            "non_finite_funding_target": "FLAT",
            "reversal_blocked_target": "FLAT",
        },
        "timing_semantics": {
            "decision_input": "finalized_bars_only",
            "score_epoch": "finalized_bar_close",
            "minimum_signal_lag_bars": MINIMUM_SIGNAL_LAG_BARS,
            "same_bar_execution": SAME_BAR_EXECUTION_ALLOWED,
            "finalized_bar_required": True,
            "pit_universe_at_score_epoch": True,
            "funding_observation_field": "funding_rate",
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
        },
        "panel_semantics": {
            "eligibility_mode": PANEL_COMPLETENESS_POLICY,
            "minimum_eligible_member_count_required": True,
            "insufficient_panel_action": "flat",
        },
        "tie_break_semantics": {
            "long_leg_order": "combined_score_desc_then_instrument_id_asc",
            "short_leg_order": "combined_score_desc_then_instrument_id_asc",
            "tie_break_policy": TIE_BREAK_POLICY,
            "combined_score_tie_leg_order": "instrument_id_asc",
        },
        "threshold_semantics": {
            "threshold_policy": THRESHOLD_POLICY,
            "min_persistence_score_for_entry_required": True,
            "decay_stability_min_ratio_required": True,
            "adverse_reversal_gate_required": True,
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


def materialize_versioned_funding_persistence_reversal_filter_ranking_semantics_binding_v0() -> (
    dict[str, Any]
):
    binding = apply_ratified_operator_bindings_v0(
        materialize_funding_persistence_reversal_filter_ranking_semantics_binding_v0()
    )
    return {
        "artifact_kind": (
            "cross_sectional_funding_rate_persistence_reversal_filter_ranking_semantics_versioned_binding"
        ),
        "artifact_version": "v0",
        "binding": binding,
        "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
    }


def serialize_versioned_binding_artifact_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(dict(envelope), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
