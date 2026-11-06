"""Portfolio binding policies for cross_sectional_futures_pairwise_lead_lag_spillover/v1.

Deterministic, versioned portfolio policy bindings derived from the ratified pairwise
spillover score/ranking contract and single-slot orchestrator compatibility.
Research-only; no runtime, order, or economic evaluation effect.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0 import (
    MIN_ELIGIBLE_MEMBERS,
    SCORE_FORMULA_VERSION,
)

INSTRUMENT_RANKING_FORMULA = "rank_instruments_by_net_inbound_spillover_desc_v1"
INSTRUMENT_DETERMINISTIC_TIE_BREAK = "score_desc_then_instrument_id_asc"
RANKING_ENTITY_SECONDARY = "instrument_net_inbound_spillover"
TIE_BREAK_SCORE_SOURCE = "unrounded_internal_score"

PACKAGE_MARKER = "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_PORTFOLIO_BINDING_V0=true"

PORTFOLIO_BINDING_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_PORTFOLIO_BINDING_IMPLEMENTATION_V0"
)
PORTFOLIO_BINDING_SCOPE = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_PORTFOLIO_BINDING_IMPLEMENTATION_V0"
)

BOUND_PORTFOLIO_BINDING_STATUS = "BOUND"
PENDING_PORTFOLIO_BINDING_STATUS = "PENDING_SEPARATE_IMPLEMENTATION_BINDING"

PRE_PORTFOLIO_BINDING_DIGEST = "6b2a74392eda2bf1a672682aa27da3873bc25666c5d9bb34d269f785afc2b438"

AGGREGATION_POLICY_VERSION = "pairwise_spillover_instrument_net_aggregation_policy.v0"
SELECTION_POLICY_VERSION = "pairwise_spillover_instrument_net_selection_policy.v0"
HOLDING_POLICY_VERSION = "pairwise_spillover_single_slot_holding_policy.v0"
EXIT_POLICY_VERSION = "pairwise_spillover_single_slot_exit_policy.v0"
PORTFOLIO_WEIGHTING_POLICY_VERSION = "pairwise_spillover_single_slot_weighting_policy.v0"

PORTFOLIO_POLICY_OWNER = (
    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0"
)
AGGREGATION_SCORE_OWNER = (
    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0."
    "compute_instrument_net_spillover_scores_v0"
)
ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"

PORTFOLIO_BINDING_REQUIRED_FIELDS: tuple[str, ...] = (
    "aggregation_policy",
    "selection_policy",
    "holding_policy",
    "exit_policy",
    "portfolio_weighting_policy",
)

REASON_PORTFOLIO_POLICY_MISSING = "MISSING_PORTFOLIO_POLICY"
REASON_PORTFOLIO_POLICY_NOT_BOUND = "PORTFOLIO_POLICY_NOT_BOUND"
REASON_PORTFOLIO_POLICY_VERSION_UNKNOWN = "PORTFOLIO_POLICY_VERSION_UNKNOWN"
REASON_PORTFOLIO_BINDING_DIGEST_MISMATCH = "PORTFOLIO_BINDING_DIGEST_MISMATCH"
REASON_BITCOIN_INSTRUMENT_SELECTION_FORBIDDEN = "BITCOIN_INSTRUMENT_SELECTION_FORBIDDEN"
REASON_NONDETERMINISTIC_SELECTION_FORBIDDEN = "NONDETERMINISTIC_SELECTION_FORBIDDEN"
REASON_IMPLICIT_DEFAULTS_FORBIDDEN = "IMPLICIT_DEFAULTS_FORBIDDEN"


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_aggregation_policy_v0() -> dict[str, Any]:
    return {
        "schema_version": AGGREGATION_POLICY_VERSION,
        "policy_version": AGGREGATION_POLICY_VERSION,
        "score_family_policy": SCORE_FORMULA_VERSION,
        "aggregation_source": "directed_pairwise_spillover_scores",
        "aggregation_target": "instrument_net_spillover_scores",
        "aggregation_callable_owner": AGGREGATION_SCORE_OWNER,
        "inbound_semantics": "sum_spillover_strength_where_instrument_is_follower",
        "outbound_semantics": "sum_spillover_strength_where_instrument_is_leader",
        "net_semantics": "inbound_sum_minus_outbound_sum",
        "missing_pair_policy": "exclude_non_finite_pair_for_epoch",
        "missing_instrument_incident_pairs_policy": "zero_contribution_when_no_incident_pairs",
        "minimum_incident_pairs_for_instrument": 0,
        "aggregation_order": "deterministic_sorted_instrument_id_asc",
        "pair_iteration_order": "leader_id_asc_then_follower_id_asc",
        "partial_pairwise_coverage_policy": "include_instrument_with_partial_incident_pairs",
        "panel_median_benchmark_aggregation_forbidden": True,
        "lead_lag_v0_aggregation_reuse_forbidden": True,
        "implicit_defaults_forbidden": True,
        "bitcoin_instruments_excluded": True,
    }


def build_selection_policy_v0() -> dict[str, Any]:
    return {
        "schema_version": SELECTION_POLICY_VERSION,
        "policy_version": SELECTION_POLICY_VERSION,
        "score_family_policy": SCORE_FORMULA_VERSION,
        "ranking_entity": RANKING_ENTITY_SECONDARY,
        "ranking_formula": INSTRUMENT_RANKING_FORMULA,
        "selection_mode": "single_top1_by_score_desc",
        "ranking_direction": "descending",
        "selection_count": 1,
        "deterministic_tie_break": INSTRUMENT_DETERMINISTIC_TIE_BREAK,
        "tie_break_score_source": TIE_BREAK_SCORE_SOURCE,
        "direction_policy": "symmetric_top1_sign",
        "positive_top1_means": "LONG_TOP1",
        "negative_top1_means": "SHORT_TOP1",
        "zero_score_target": "FLAT",
        "non_finite_score_target": "FLAT",
        "minimum_rankable_instrument_count": MIN_ELIGIBLE_MEMBERS,
        "insufficient_panel_policy": "FAIL_CLOSED_EMPTY_RANKING",
        "insufficient_panel_target": "FLAT",
        "bitcoin_instruments_forbidden": True,
        "missing_score_policy": "exclude_non_finite",
        "finalized_bar_only": True,
        "nondeterministic_selection_forbidden": True,
        "post_result_selection_forbidden": True,
        "implicit_defaults_forbidden": True,
        "orchestrator_owner": ORCHESTRATOR_OWNER,
    }


def build_holding_policy_v0() -> dict[str, Any]:
    return {
        "schema_version": HOLDING_POLICY_VERSION,
        "policy_version": HOLDING_POLICY_VERSION,
        "rebalance_interval_bars": 1,
        "rebalance_policy_class": "fixed_N_bar_cadence",
        "rebalance_cadence": "PT1H",
        "hold_semantics": "until_next_rebalance",
        "minimum_hold_epochs": 0,
        "between_rebalance_behavior": "maintain_position_until_rebalance_or_exit_trigger",
        "stale_instrument_policy": "exclude_when_ineligible_for_epoch",
        "missing_data_between_rebalances": "force_flat_if_selected_instrument_missing",
        "warmup_incomplete_target": "FLAT",
        "implicit_defaults_forbidden": True,
    }


def build_exit_policy_v0() -> dict[str, Any]:
    return {
        "schema_version": EXIT_POLICY_VERSION,
        "policy_version": EXIT_POLICY_VERSION,
        "rank_based_exit": True,
        "invalid_data_exit": "force_flat_on_non_finite_score",
        "universe_removal_exit": "force_flat_on_universe_removal",
        "rebalance_exit": "rotation_via_switch_policy",
        "switch_policy": "flat_then_wait_one_epoch_then_enter",
        "switch_entry_delay_epochs": 1,
        "atomic_side_switch_forbidden": True,
        "opposite_side_requires_reconciled_flat": True,
        "direct_reversal_without_flat_forbidden": True,
        "end_of_window_policy": "force_close_at_window_end_inclusive_v0",
        "cooldown_policy": "no_cooldown",
        "runtime_order_semantics_forbidden": True,
        "implicit_defaults_forbidden": True,
    }


def build_portfolio_weighting_policy_v0() -> dict[str, Any]:
    return {
        "schema_version": PORTFOLIO_WEIGHTING_POLICY_VERSION,
        "policy_version": PORTFOLIO_WEIGHTING_POLICY_VERSION,
        "weighting_policy": "equal_weight_single_slot_v0",
        "gross_exposure_policy": "unit_notional_single_slot_v0",
        "net_exposure_policy": "directional_single_slot_v0",
        "per_instrument_cap": 1.0,
        "portfolio_cap": 1.0,
        "gross_exposure_cap": 1.0,
        "net_exposure_bounds": {"min": -1.0, "max": 1.0},
        "long_budget": 1.0,
        "short_budget": 1.0,
        "empty_selection_weight": "flat_zero_exposure",
        "partial_selection_policy": "not_applicable_single_slot",
        "rounding_policy": "deterministic_no_rounding_required_single_unit",
        "weight_normalization": "single_instrument_full_notional",
        "weight_sum_invariant": 1.0,
        "exposure_invariant_enforced": True,
        "risk_sizing_semantics_changed": False,
        "implicit_defaults_forbidden": True,
    }


def compute_aggregation_policy_digest_v0(
    policy: Mapping[str, Any] | None = None,
) -> str:
    return _stable_digest(dict(policy or build_aggregation_policy_v0()))


def compute_selection_policy_digest_v0(
    policy: Mapping[str, Any] | None = None,
) -> str:
    return _stable_digest(dict(policy or build_selection_policy_v0()))


def compute_holding_policy_digest_v0(
    policy: Mapping[str, Any] | None = None,
) -> str:
    return _stable_digest(dict(policy or build_holding_policy_v0()))


def compute_exit_policy_digest_v0(
    policy: Mapping[str, Any] | None = None,
) -> str:
    return _stable_digest(dict(policy or build_exit_policy_v0()))


def compute_portfolio_weighting_policy_digest_v0(
    policy: Mapping[str, Any] | None = None,
) -> str:
    return _stable_digest(dict(policy or build_portfolio_weighting_policy_v0()))


def _bound_policy_field(
    *,
    ref: str,
    policy: Mapping[str, Any],
    digest: str,
) -> dict[str, Any]:
    return {
        "status": BOUND_PORTFOLIO_BINDING_STATUS,
        "ref": ref,
        "binding_digest": digest,
        "policy_version": policy.get("policy_version", ""),
        "policy": dict(policy),
    }


def build_portfolio_implementation_bindings_v0() -> dict[str, Any]:
    aggregation = build_aggregation_policy_v0()
    selection = build_selection_policy_v0()
    holding = build_holding_policy_v0()
    exit_policy = build_exit_policy_v0()
    weighting = build_portfolio_weighting_policy_v0()
    return {
        "binding_version": "v0",
        "portfolio_binding_scope": "COMPLETE",
        "portfolio_rules_forbidden_in_binding_scope": False,
        "numeric_lags_forbidden_in_binding_scope": True,
        "numeric_thresholds_forbidden_in_binding_scope": True,
        "aggregation_policy": _bound_policy_field(
            ref="aggregation_policy",
            policy=aggregation,
            digest=compute_aggregation_policy_digest_v0(aggregation),
        ),
        "selection_policy": _bound_policy_field(
            ref="selection_policy",
            policy=selection,
            digest=compute_selection_policy_digest_v0(selection),
        ),
        "holding_policy": _bound_policy_field(
            ref="holding_policy",
            policy=holding,
            digest=compute_holding_policy_digest_v0(holding),
        ),
        "exit_policy": _bound_policy_field(
            ref="exit_policy",
            policy=exit_policy,
            digest=compute_exit_policy_digest_v0(exit_policy),
        ),
        "portfolio_weighting_policy": _bound_policy_field(
            ref="portfolio_weighting_policy",
            policy=weighting,
            digest=compute_portfolio_weighting_policy_digest_v0(weighting),
        ),
    }


def build_portfolio_policy_contracts_v0() -> dict[str, Any]:
    return {
        "schema_version": "pairwise_spillover_portfolio_policy_contracts.v0",
        "aggregation_policy": build_aggregation_policy_v0(),
        "selection_policy": build_selection_policy_v0(),
        "holding_policy": build_holding_policy_v0(),
        "exit_policy": build_exit_policy_v0(),
        "portfolio_weighting_policy": build_portfolio_weighting_policy_v0(),
    }


def build_portfolio_digest_dependency_graph_v0(
    *,
    aggregation_digest: str,
    selection_digest: str,
    holding_digest: str,
    exit_digest: str,
    weighting_digest: str,
    portfolio_bindings_digest: str,
) -> dict[str, Any]:
    return {
        "schema_version": "portfolio_binding_digest_graph.v0",
        "edges": [
            {"from": "aggregation_policy", "to": "portfolio_bindings_digest"},
            {"from": "selection_policy", "to": "portfolio_bindings_digest"},
            {"from": "holding_policy", "to": "portfolio_bindings_digest"},
            {"from": "exit_policy", "to": "portfolio_bindings_digest"},
            {"from": "portfolio_weighting_policy", "to": "portfolio_bindings_digest"},
            {"from": "portfolio_bindings_digest", "to": "config_digest"},
            {"from": "config_digest", "to": "binding_digest"},
        ],
        "component_digests": {
            "aggregation_policy_digest": aggregation_digest,
            "selection_policy_digest": selection_digest,
            "holding_policy_digest": holding_digest,
            "exit_policy_digest": exit_digest,
            "portfolio_weighting_policy_digest": weighting_digest,
            "portfolio_bindings_digest": portfolio_bindings_digest,
        },
    }


def compute_portfolio_bindings_digest_v0(
    bindings: Mapping[str, Any] | None = None,
) -> str:
    active = dict(bindings or build_portfolio_implementation_bindings_v0())
    payload = {field: active.get(field, {}) for field in PORTFOLIO_BINDING_REQUIRED_FIELDS}
    return _stable_digest(payload)


def validate_portfolio_policy_version_v0(
    policy: Mapping[str, Any],
    *,
    expected_version: str,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if policy.get("policy_version") != expected_version:
        reasons.append(REASON_PORTFOLIO_POLICY_VERSION_UNKNOWN)
    if policy.get("implicit_defaults_forbidden") is not True:
        reasons.append(REASON_IMPLICIT_DEFAULTS_FORBIDDEN)
    return not reasons, tuple(dict.fromkeys(reasons))


def validate_aggregation_policy_v0(policy: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    ok, reasons = validate_portfolio_policy_version_v0(
        policy, expected_version=AGGREGATION_POLICY_VERSION
    )
    extra: list[str] = list(reasons)
    if policy.get("bitcoin_instruments_excluded") is not True:
        extra.append(REASON_BITCOIN_INSTRUMENT_SELECTION_FORBIDDEN)
    return not extra, tuple(dict.fromkeys(extra))


def validate_selection_policy_v0(policy: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    ok, reasons = validate_portfolio_policy_version_v0(
        policy, expected_version=SELECTION_POLICY_VERSION
    )
    extra: list[str] = list(reasons)
    if policy.get("bitcoin_instruments_forbidden") is not True:
        extra.append(REASON_BITCOIN_INSTRUMENT_SELECTION_FORBIDDEN)
    if policy.get("nondeterministic_selection_forbidden") is not True:
        extra.append(REASON_NONDETERMINISTIC_SELECTION_FORBIDDEN)
    if not policy.get("deterministic_tie_break"):
        extra.append("MISSING_DETERMINISTIC_TIE_BREAK")
    return not extra, tuple(dict.fromkeys(extra))


def validate_holding_policy_v0(policy: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    return validate_portfolio_policy_version_v0(policy, expected_version=HOLDING_POLICY_VERSION)


def validate_exit_policy_v0(policy: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    ok, reasons = validate_portfolio_policy_version_v0(policy, expected_version=EXIT_POLICY_VERSION)
    extra: list[str] = list(reasons)
    if policy.get("runtime_order_semantics_forbidden") is not True:
        extra.append("RUNTIME_ORDER_SEMANTICS_NOT_FORBIDDEN")
    if policy.get("direct_reversal_without_flat_forbidden") is not True:
        extra.append("DIRECT_REVERSAL_NOT_FORBIDDEN")
    return not extra, tuple(dict.fromkeys(extra))


def validate_portfolio_weighting_policy_v0(
    policy: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    ok, reasons = validate_portfolio_policy_version_v0(
        policy, expected_version=PORTFOLIO_WEIGHTING_POLICY_VERSION
    )
    extra: list[str] = list(reasons)
    if policy.get("risk_sizing_semantics_changed") is not False:
        extra.append("RISK_SIZING_SEMANTICS_CHANGED")
    if policy.get("weight_sum_invariant") != 1.0:
        extra.append("WEIGHT_SUM_INVARIANT_VIOLATION")
    return not extra, tuple(dict.fromkeys(extra))


def validate_portfolio_implementation_bindings_v0(
    bindings: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    validators = {
        "aggregation_policy": (
            validate_aggregation_policy_v0,
            compute_aggregation_policy_digest_v0,
        ),
        "selection_policy": (validate_selection_policy_v0, compute_selection_policy_digest_v0),
        "holding_policy": (validate_holding_policy_v0, compute_holding_policy_digest_v0),
        "exit_policy": (validate_exit_policy_v0, compute_exit_policy_digest_v0),
        "portfolio_weighting_policy": (
            validate_portfolio_weighting_policy_v0,
            compute_portfolio_weighting_policy_digest_v0,
        ),
    }
    for field, (validator, digest_fn) in validators.items():
        binding = bindings.get(field)
        if not isinstance(binding, Mapping):
            reasons.append(f"{REASON_PORTFOLIO_POLICY_MISSING}:{field}")
            continue
        if binding.get("status") != BOUND_PORTFOLIO_BINDING_STATUS:
            reasons.append(f"{REASON_PORTFOLIO_POLICY_NOT_BOUND}:{field}")
            continue
        policy = binding.get("policy", {})
        if not isinstance(policy, Mapping):
            reasons.append(f"{REASON_PORTFOLIO_POLICY_MISSING}:{field}.policy")
            continue
        ok, policy_reasons = validator(policy)
        if not ok:
            reasons.extend(f"{item}:{field}" for item in policy_reasons)
        expected_digest = digest_fn(policy)
        if str(binding.get("binding_digest", "")) != expected_digest:
            reasons.append(f"{REASON_PORTFOLIO_BINDING_DIGEST_MISMATCH}:{field}")
    return not reasons, tuple(dict.fromkeys(reasons))


def build_portfolio_field_classification_v0() -> dict[str, Any]:
    return {
        "schema_version": "field_classification.v0",
        "aggregation_policy": {
            "field_path": "pending_implementation_bindings.aggregation_policy",
            "field_class": "AUTHORED_SEMANTIC_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "selection_policy": {
            "field_path": "pending_implementation_bindings.selection_policy",
            "field_class": "AUTHORED_SEMANTIC_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "holding_policy": {
            "field_path": "pending_implementation_bindings.holding_policy",
            "field_class": "AUTHORED_SEMANTIC_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "exit_policy": {
            "field_path": "pending_implementation_bindings.exit_policy",
            "field_class": "AUTHORED_SEMANTIC_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "portfolio_weighting_policy": {
            "field_path": "pending_implementation_bindings.portfolio_weighting_policy",
            "field_class": "AUTHORED_SEMANTIC_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "aggregation_policy_digest": {
            "field_path": "pending_implementation_bindings.aggregation_policy.binding_digest",
            "field_class": "DERIVED_DIGEST_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "selection_policy_digest": {
            "field_path": "pending_implementation_bindings.selection_policy.binding_digest",
            "field_class": "DERIVED_DIGEST_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "holding_policy_digest": {
            "field_path": "pending_implementation_bindings.holding_policy.binding_digest",
            "field_class": "DERIVED_DIGEST_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "exit_policy_digest": {
            "field_path": "pending_implementation_bindings.exit_policy.binding_digest",
            "field_class": "DERIVED_DIGEST_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "portfolio_weighting_policy_digest": {
            "field_path": (
                "pending_implementation_bindings.portfolio_weighting_policy.binding_digest"
            ),
            "field_class": "DERIVED_DIGEST_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "portfolio_bindings_digest": {
            "field_path": "portfolio_bindings_digest",
            "field_class": "DERIVED_DIGEST_FIELD",
            "canonical_owner": PORTFOLIO_POLICY_OWNER,
        },
        "binding_digest": {
            "field_path": "binding_digest",
            "field_class": "DERIVED_DIGEST_FIELD",
            "canonical_owner": (
                "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
                "versioned_hypothesis_binding_v0"
            ),
        },
        "unclassified_changed_field_count": 0,
    }


def build_portfolio_reuse_decision_v0() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decisions": [
            {
                "component": "instrument_net_aggregation",
                "decision": "REUSE_AS_IS",
                "owner": AGGREGATION_SCORE_OWNER,
            },
            {
                "component": "ranking_tie_break_semantics",
                "decision": "REUSE_AS_IS",
                "owner": (
                    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
                    "score_and_ranking_contract_v0"
                ),
            },
            {
                "component": "single_slot_orchestrator_holding_exit_weighting",
                "decision": "REUSE_WITH_NARROW_ADAPTER",
                "owner": ORCHESTRATOR_OWNER,
                "justification": "instrument_net_inbound_secondary_ranking_to_single_slot",
            },
            {
                "component": "portfolio_policy_authorship",
                "decision": "NEW_IMPLEMENTATION_JUSTIFIED",
                "owner": PORTFOLIO_POLICY_OWNER,
                "justification": "pairwise_spillover_specific_portfolio_semantics_not_in_prior_slices",
            },
        ],
    }
