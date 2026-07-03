"""Funding-rate cross-sectional ranking semantics declarative binding schema (v0).

Pure offline schema materialization for ratified funding-carry policy classes.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from enum import Enum
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_RANKING_SEMANTICS_BINDING_V0=true"
SCHEMA_VERSION = "cross_sectional_funding_rate_ranking_semantics_binding.v0"
HYPOTHESIS_ID = "CROSS_SECTIONAL_FUNDING_RATE_CARRY_NON_BITCOIN_PERPETUALS_V0"

SCORE_FAMILY_POLICY = "cross_sectional_funding_rate_rank_long_low_short_high"
DIRECTION_POLICY = "long_low_funding_short_high_funding"
SELECTION_MODE = "funding_extremes_single_leg_rotation_v0"
LONG_LEG_MEANS = "LONG_LOWEST_FUNDING"
SHORT_LEG_MEANS = "SHORT_HIGHEST_FUNDING"

SIGNAL_TIMING_POLICY = "finalized_bar_close_epoch"
MINIMUM_SIGNAL_LAG_BARS = 1
SAME_BAR_EXECUTION_ALLOWED = False
REBALANCE_POLICY_CLASS = "fixed_N_bar_cadence"
SWITCH_POLICY = "flat_then_wait_one_epoch_then_enter"
COOLDOWN_POLICY = "no_cooldown"
MINIMUM_HOLD_POLICY = "until_next_rebalance"
PANEL_COMPLETENESS_POLICY = "per_instrument_eligibility_mask"
MISSING_BAR_POLICY = "exclude_non_selected_instrument_for_epoch"
TIE_BREAK_POLICY = "funding_rate_asc_then_instrument_id_asc_for_long_leg"
THRESHOLD_POLICY = "rank_extremes_only_no_continuous_threshold_tuning"

ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"
ORCHESTRATOR_SCOPE = "RESEARCH_ONLY"

NUMERIC_BINDING_KEYS = (
    "funding_smoothing_window_bars",
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
)

VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/cross_sectional_funding_rate_carry_v0_ranking_semantics_binding_v0.json"
)

RATIFIED_OPERATOR_BINDING_VALUES: dict[str, int | float | str] = {
    "funding_smoothing_window_bars": 1,
    "rebalance_interval_bars": 1,
    "signal_lag_bars": 1,
    "min_eligible_members_for_rank": 5,
    "switch_entry_delay_epochs": 1,
    "max_bar_staleness_bars": 1,
}

RATIFIED_OPERATOR_RATIONALES: dict[str, str] = {
    "funding_smoothing_window_bars": (
        "Funding wird ohne Glättung auf der finalisierten Lag-Bar gelesen "
        "(Fenster=1). Keine implizite Übernahme aus Preis-Momentum-Defaults."
    ),
    "rebalance_interval_bars": (
        "Ranking wird in jeder finalisierten Epoche neu berechnet; keine "
        "Order- oder Runtime-Wirkung."
    ),
    "signal_lag_bars": (
        "Ein vollständiger Bar-Lag verhindert Look-ahead auf Funding-Observations."
    ),
    "min_eligible_members_for_rank": (
        "Mindestens fünf gleichzeitig zulässige Panel-Mitglieder für "
        "Cross-Sectional-Funding-Ranking."
    ),
    "switch_entry_delay_epochs": (
        "Nach Leg-Wechsel eine Epoche Wartezeit vor Entry — analog cs-rs Switch-Policy."
    ),
    "max_bar_staleness_bars": (
        "Höchstens eine Bar Staleness-Toleranz; ältere Mitglieder werden exkludiert."
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

ENVELOPE_DIGEST_STATUS_REQUIRED_UNBOUND = "REQUIRED_UNBOUND_DIGEST"


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


def materialize_funding_rate_ranking_semantics_binding_v0() -> dict[str, Any]:
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
            "panel_insufficient_target": "FLAT",
            "warmup_incomplete_target": "FLAT",
            "non_finite_funding_target": "FLAT",
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
            "long_leg_order": "funding_rate_asc_then_instrument_id_asc",
            "short_leg_order": "funding_rate_desc_then_instrument_id_asc",
            "tie_break_policy": TIE_BREAK_POLICY,
        },
        "threshold_semantics": {
            "threshold_policy": THRESHOLD_POLICY,
            "numeric_strength_threshold_initial": False,
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


def materialize_versioned_funding_rate_ranking_semantics_binding_v0() -> dict[str, Any]:
    binding = apply_ratified_operator_bindings_v0(
        materialize_funding_rate_ranking_semantics_binding_v0()
    )
    return {
        "artifact_kind": "cross_sectional_funding_rate_ranking_semantics_versioned_binding",
        "artifact_version": "v0",
        "binding": binding,
        "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
    }


def serialize_versioned_binding_artifact_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(dict(envelope), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
