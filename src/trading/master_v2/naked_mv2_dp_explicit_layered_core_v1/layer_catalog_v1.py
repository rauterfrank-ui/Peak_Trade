"""Canonical L1–L10 layer catalog for naked MV2+DP explicit layered core v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Tuple

EXPLICIT_LAYERED_CORE_VERSION = "naked_mv2_dp_explicit_layered_core/v1"
EXPLICIT_LAYERED_CORE_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1"


class LayerIdV1(str, Enum):
    L1_SELECTED_FUTURE = "L1_SELECTED_FUTURE"
    L2_MARKET_OBSERVATION = "L2_MARKET_OBSERVATION"
    L3_INITIAL_DIRECTION = "L3_INITIAL_DIRECTION"
    L4_INITIAL_STATE_INITIALIZATION = "L4_INITIAL_STATE_INITIALIZATION"
    L5_NULLLINE = "L5_NULLLINE"
    L6_DYNAMIC_SCOPE_GENERATOR = "L6_DYNAMIC_SCOPE_GENERATOR"
    L7_SCOPE_STATE = "L7_SCOPE_STATE"
    L8_RUNNING_REFERENCE = "L8_RUNNING_REFERENCE"
    L9_COUNTER_MOVE = "L9_COUNTER_MOVE"
    L10_BULL_BEAR_STATE_SWITCH = "L10_BULL_BEAR_STATE_SWITCH"


@dataclass(frozen=True)
class LayerCatalogEntryV1:
    layer_id: LayerIdV1
    semantic_owner: str
    input_summary: str
    output_summary: str
    mutates: str
    downstream_consumer: str


def _entry(
    layer: LayerIdV1,
    *,
    owner_suffix: str,
    inp: str,
    out: str,
    mutates: str,
    downstream: str,
) -> LayerCatalogEntryV1:
    return LayerCatalogEntryV1(
        layer_id=layer,
        semantic_owner=f"{EXPLICIT_LAYERED_CORE_OWNER}.{owner_suffix}",
        input_summary=inp,
        output_summary=out,
        mutates=mutates,
        downstream_consumer=downstream,
    )


LAYER_CATALOG_V1: Mapping[LayerIdV1, LayerCatalogEntryV1] = {
    LayerIdV1.L1_SELECTED_FUTURE: _entry(
        LayerIdV1.L1_SELECTED_FUTURE,
        owner_suffix="l1_selected_future_v1",
        inp="instrument_selection_request",
        out="selected_future_binding",
        mutates="selected_future_state_only",
        downstream="L2_MARKET_OBSERVATION",
    ),
    LayerIdV1.L2_MARKET_OBSERVATION: _entry(
        LayerIdV1.L2_MARKET_OBSERVATION,
        owner_suffix="l2_market_observation_v1",
        inp="selected_future + observation_candidate",
        out="accepted_market_observation",
        mutates="observation_acceptance_state_only",
        downstream="L3_INITIAL_DIRECTION",
    ),
    LayerIdV1.L3_INITIAL_DIRECTION: _entry(
        LayerIdV1.L3_INITIAL_DIRECTION,
        owner_suffix="l3_initial_direction_v1",
        inp="consecutive_distinct_observations",
        out="elementary_direction_result",
        mutates="none_pure_evaluator",
        downstream="L4_INITIAL_STATE_INITIALIZATION",
    ),
    LayerIdV1.L4_INITIAL_STATE_INITIALIZATION: _entry(
        LayerIdV1.L4_INITIAL_STATE_INITIALIZATION,
        owner_suffix="l4_initial_state_v1",
        inp="non_neutral_elementary_direction",
        out="initial_bull_or_bear_regime",
        mutates="regime_authority_established_once",
        downstream="L5_NULLLINE",
    ),
    LayerIdV1.L5_NULLLINE: _entry(
        LayerIdV1.L5_NULLLINE,
        owner_suffix="l5_nullline_v1",
        inp="initialization_mark_at_regime_birth",
        out="nullline_price_basis",
        mutates="nullline_state_only_not_running_reference",
        downstream="L6_DYNAMIC_SCOPE_GENERATOR",
    ),
    LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR: _entry(
        LayerIdV1.L6_DYNAMIC_SCOPE_GENERATOR,
        owner_suffix="l6_dynamic_scope_generator_v1",
        inp="nullline_context + external_d_t_proposal",
        out="validated_d_t_or_fail_closed",
        mutates="none_replaceable_generator",
        downstream="L7_SCOPE_STATE",
    ),
    LayerIdV1.L7_SCOPE_STATE: _entry(
        LayerIdV1.L7_SCOPE_STATE,
        owner_suffix="l7_scope_state_v1",
        inp="validated_d_t + nullline_provenance",
        out="materialized_scope_state",
        mutates="scope_state_only_no_regime_switch",
        downstream="L8_RUNNING_REFERENCE",
    ),
    LayerIdV1.L8_RUNNING_REFERENCE: _entry(
        LayerIdV1.L8_RUNNING_REFERENCE,
        owner_suffix="l8_running_reference_v1",
        inp="regime + mark + prior_running_reference",
        out="updated_running_reference_r_t",
        mutates="running_reference_state_only_not_nullline",
        downstream="L9_COUNTER_MOVE",
    ),
    LayerIdV1.L9_COUNTER_MOVE: _entry(
        LayerIdV1.L9_COUNTER_MOVE,
        owner_suffix="l9_counter_move_v1",
        inp="regime + mark + running_reference",
        out="counter_move_cm_t",
        mutates="none_pure_formula",
        downstream="L10_BULL_BEAR_STATE_SWITCH",
    ),
    LayerIdV1.L10_BULL_BEAR_STATE_SWITCH: _entry(
        LayerIdV1.L10_BULL_BEAR_STATE_SWITCH,
        owner_suffix="l10_bull_bear_switch_v1",
        inp="cm_t + scope_d_t + prior_regime",
        out="regime_post + r_t_reset_flag",
        mutates="regime_switch_authority_sole_price_rule",
        downstream="orchestrator_persisted_state",
    ),
}


LAYER_ORDER_V1: Tuple[LayerIdV1, ...] = tuple(LayerIdV1)


__all__ = [
    "EXPLICIT_LAYERED_CORE_VERSION",
    "EXPLICIT_LAYERED_CORE_OWNER",
    "LayerIdV1",
    "LayerCatalogEntryV1",
    "LAYER_CATALOG_V1",
    "LAYER_ORDER_V1",
]
