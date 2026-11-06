"""Funding-rate dual-leg spread cross-sectional ranking semantics declarative binding schema (v1)."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from enum import Enum
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_RANKING_SEMANTICS_BINDING_V1=true"
SCHEMA_VERSION = "cross_sectional_funding_rate_dual_leg_spread_ranking_semantics_binding.v1"
HYPOTHESIS_ID = "CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_NON_BITCOIN_PERPETUALS_V1"

SCORE_FAMILY_POLICY = "cross_sectional_funding_rate_level_spread_dual_leg_v1"
DIRECTION_POLICY = "symmetric_funding_level_spread_dual_leg_simultaneous_v1"
SELECTION_MODE = "funding_level_spread_dual_leg_simultaneous_v1"
LONG_LEG_MEANS = "LONG_LOWEST_FUNDING_RATE"
SHORT_LEG_MEANS = "SHORT_HIGHEST_FUNDING_RATE"

SIGNAL_TIMING_POLICY = "finalized_bar_close_epoch"
MINIMUM_SIGNAL_LAG_BARS = 1
SAME_BAR_EXECUTION_ALLOWED = False
REBALANCE_POLICY_CLASS = "fixed_N_bar_cadence"
SWITCH_POLICY = "simultaneous_dual_leg_rebalance_v1"
COOLDOWN_POLICY = "no_cooldown"
MINIMUM_HOLD_POLICY = "until_next_rebalance"
PANEL_COMPLETENESS_POLICY = "per_instrument_eligibility_mask"
MISSING_BAR_POLICY = "exclude_non_selected_instrument_for_epoch"
TIE_BREAK_POLICY = "funding_rate_asc_then_instrument_id_asc_for_long_leg"
THRESHOLD_POLICY = "min_spread_bps_admissibility_gate_frozen_at_ratification"

ORCHESTRATOR_OWNER = "cross_sectional_funding_rate_dual_leg_spread_research_orchestrator_v1"
ORCHESTRATOR_SCOPE = "RESEARCH_ONLY"

NUMERIC_BINDING_KEYS = (
    "rebalance_interval_bars",
    "signal_lag_bars",
    "min_eligible_members_for_rank",
    "switch_entry_delay_epochs",
    "max_bar_staleness_bars",
    "min_spread_bps_for_entry",
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
)

VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_funding_rate_dual_leg_spread_v1_ranking_semantics_binding_v0.json"
)

RATIFIED_OPERATOR_BINDING_VALUES: dict[str, int | float | str] = {
    "rebalance_interval_bars": 1,
    "signal_lag_bars": 1,
    "min_eligible_members_for_rank": 5,
    "switch_entry_delay_epochs": 1,
    "max_bar_staleness_bars": 1,
    "min_spread_bps_for_entry": 0.5,
}

RATIFIED_OPERATOR_RATIONALES: dict[str, str] = {
    "rebalance_interval_bars": (
        "Ranking recomputed every finalized epoch; research-only, no runtime effect."
    ),
    "signal_lag_bars": ("One full bar lag prevents look-ahead on funding observations."),
    "min_eligible_members_for_rank": (
        "At least five simultaneously eligible panel members for cross-sectional spread."
    ),
    "switch_entry_delay_epochs": (
        "After spread leg change wait one epoch before entry per switch policy."
    ),
    "max_bar_staleness_bars": ("At most one bar staleness tolerance; older members excluded."),
    "min_spread_bps_for_entry": (
        "Frozen 0.5 bps minimum funding spread between long and short legs; no post-hoc tuning."
    ),
}

PR4925_EXCLUDED_SELECTION_MODE = "funding_delta_extremes_single_leg_rotation_v0"


def compute_operator_decision_digest_v1(
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


ATTESTED_OPERATOR_DECISION_DIGEST = compute_operator_decision_digest_v1()


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


def materialize_funding_rate_dual_leg_spread_ranking_semantics_binding_v1() -> dict[str, Any]:
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
            "dual_leg_simultaneous_required": True,
            "dual_leg_simultaneous_forbidden": False,
            "single_slot_rotation": False,
            "single_slot_rotation_forbidden": True,
            "panel_insufficient_target": "FLAT",
            "warmup_incomplete_target": "FLAT",
            "non_finite_funding_target": "FLAT",
            "spread_below_min_target": "FLAT",
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
            "simultaneous_dual_leg_rebalance": True,
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
            "long_leg_order": "funding_rate_asc_then_instrument_id_asc",
            "short_leg_order": "funding_rate_desc_then_instrument_id_asc",
            "tie_break_policy": TIE_BREAK_POLICY,
        },
        "threshold_semantics": {
            "threshold_policy": THRESHOLD_POLICY,
            "min_spread_bps_for_entry_required": True,
        },
        "material_difference_vs_pr4925": {
            "pr4925_selection_mode_excluded": PR4925_EXCLUDED_SELECTION_MODE,
            "pr4925_dual_leg_simultaneous_forbidden": True,
            "v1_dual_leg_simultaneous_required": True,
            "v1_funding_delta_lookback_forbidden": True,
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


def compute_config_digest_v1(config_bytes: bytes) -> str:
    return hashlib.sha256(config_bytes).hexdigest()


def apply_ratified_operator_bindings_v1(binding: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(binding)
    numeric = result["numeric_bindings"]
    for key, value in RATIFIED_OPERATOR_BINDING_VALUES.items():
        numeric[key] = _field(BindingFieldStatus.BOUND, value=value)
    status = result["binding_status"]
    status["numeric_bindings_status"] = AggregateBindingStatus.BOUND.value
    status["overall_binding_status"] = AggregateBindingStatus.INCOMPLETE_FAIL_CLOSED.value
    return result


def materialize_versioned_funding_rate_dual_leg_spread_ranking_semantics_binding_v1() -> dict[
    str, Any
]:
    binding = apply_ratified_operator_bindings_v1(
        materialize_funding_rate_dual_leg_spread_ranking_semantics_binding_v1()
    )
    return {
        "artifact_kind": "cross_sectional_funding_rate_dual_leg_spread_ranking_semantics_versioned_binding",
        "artifact_version": "v1",
        "binding": binding,
        "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
    }


def serialize_versioned_binding_artifact_json_v1(envelope: Mapping[str, Any]) -> str:
    return json.dumps(dict(envelope), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
