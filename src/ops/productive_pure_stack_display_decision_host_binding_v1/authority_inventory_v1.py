"""Fail-closed inventory of Pure-Stack display input authorities on the host."""

from __future__ import annotations

from typing import Tuple

from src.ops.productive_pure_stack_display_decision_host_binding_v1.constants_v1 import (
    INPUT_AUTHORITY_CAPITAL_SLOT_CONFIG,
    INPUT_AUTHORITY_CAPITAL_SLOT_STATE_INIT,
    INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT,
    INPUT_AUTHORITY_SUITABILITY_PROJECTION,
    INPUT_AUTHORITY_SURVIVAL_ENVELOPE,
    INPUT_AUTHORITY_TRANSITION_DECISION_PASSTHROUGH,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.models_v1 import (
    PureStackInputAuthorityProbeV1,
)


def probe_pure_stack_display_input_authorities_v1() -> Tuple[PureStackInputAuthorityProbeV1, ...]:
    """Return explicit authority probes — never invent missing owners."""
    return (
        PureStackInputAuthorityProbeV1(
            input_name="FuturesInputSnapshot",
            authority_present=INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT,
            authority_owner="",
            detail=(
                "No ratified productive FuturesInputSnapshot builder bound to "
                "run_bridge_cycle_v1; CMC→Snapshot conversion unauthorized; "
                "scenario/WebUI builders forbidden"
            ),
        ),
        PureStackInputAuthorityProbeV1(
            input_name="DoublePlaySurvivalEnvelope",
            authority_present=INPUT_AUTHORITY_SURVIVAL_ENVELOPE,
            authority_owner="",
            detail=(
                "No ratified productive SurvivalEnvelope fingerprint/limits owner; "
                "SurvivalResultV1 mapping unauthorized; scenario fixtures forbidden"
            ),
        ),
        PureStackInputAuthorityProbeV1(
            input_name="SuitabilityProjectionInput",
            authority_present=INPUT_AUTHORITY_SUITABILITY_PROJECTION,
            authority_owner="",
            detail=(
                "No ratified productive StrategyMetadata/InstrumentIntelligence "
                "owner for project_strategy_suitability; SuitabilityResultV1 "
                "mapping unauthorized"
            ),
        ),
        PureStackInputAuthorityProbeV1(
            input_name="CapitalSlotConfig",
            authority_present=INPUT_AUTHORITY_CAPITAL_SLOT_CONFIG,
            authority_owner="",
            detail=(
                "CanonicalDecisionRuntimeConfigV1 has no capital-slot fields; "
                "no productive CapitalSlotConfig owner ratified"
            ),
        ),
        PureStackInputAuthorityProbeV1(
            input_name="CapitalSlotState",
            authority_present=INPUT_AUTHORITY_CAPITAL_SLOT_STATE_INIT,
            authority_owner="",
            detail=(
                "No ratified productive CapitalSlotState initialization authority; "
                "accounting/portfolio equity remapping unauthorized"
            ),
        ),
        PureStackInputAuthorityProbeV1(
            input_name="TransitionDecision",
            authority_present=INPUT_AUTHORITY_TRANSITION_DECISION_PASSTHROUGH,
            authority_owner=("trading.master_v2.double_play_state.transition_state"),
            detail=(
                "Produced inside run_integrated_offline_trading_logic_replay_v1; "
                "identical object passthrough authorized"
            ),
        ),
    )


def missing_input_authorities_v1() -> Tuple[str, ...]:
    return tuple(
        p.input_name
        for p in probe_pure_stack_display_input_authorities_v1()
        if not p.authority_present
    )


def all_required_input_authorities_present_v1() -> bool:
    return len(missing_input_authorities_v1()) == 0
