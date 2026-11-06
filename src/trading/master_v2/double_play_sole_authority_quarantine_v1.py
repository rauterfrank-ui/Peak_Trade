# src/trading/master_v2/double_play_sole_authority_quarantine_v1.py
"""
Double Play Sole Authority Fail-Closed Quarantine v1.

Freezes Master V2 / Double Play as the sole Bull/Bear SideState and Switch
authority on productive canonical paths. Competing Ops switch-gate decisions,
unmarked scenario scope-event injection, and backtest SideState overwrite are
fail-closed disabled or quarantined as TEST_ONLY / OBSERVATION_ONLY.

CHOP is bound as scope policy (see chop_scope_event_policy_binding_v1).
UNKNOWN remains NOT_BOUND_FAIL_CLOSED. No Live/Orders/Runtime activation.
"""

from __future__ import annotations

from typing import Mapping

DOUBLE_PLAY_SOLE_AUTHORITY_QUARANTINE_LAYER_VERSION = "v1"
DOUBLE_PLAY_SOLE_AUTHORITY_QUARANTINE_OWNER = (
    "trading.master_v2.double_play_sole_authority_quarantine_v1"
)
PACKAGE_MARKER = "DOUBLE_PLAY_SOLE_AUTHORITY_QUARANTINE_V1=true"

CANONICAL_BULL_BEAR_STATE_OWNER = "trading.master_v2.double_play_state.transition_state"
CANONICAL_SWITCH_AUTHORITY = "trading.master_v2.double_play_state.transition_state"
CANONICAL_SCOPE_STATE_OWNER = "trading.master_v2.double_play_state.RuntimeScopeState"
CANONICAL_SCOPE_IDENTITY_OWNER = (
    "trading.master_v2.canonical_scope_initialization_v1.CanonicalScopeSnapshotV1"
)
CANONICAL_OFFLINE_ORCHESTRATOR = "trading.master_v2.integrated_offline_trading_logic_replay_v1"
CANONICAL_COMPOSITION_AUTHORITY = "trading.master_v2.double_play_composition_matrix_v1"

OPS_EVALUATE_DOUBLE_PLAY_ROLE = "PROJECTION_DIAGNOSTIC_ONLY"
OPS_SWITCH_GATE_AUTHORITY_STATUS = "FAIL_CLOSED_DISABLED_FOR_DOUBLE_PLAY"
OPS_SWITCH_AUTHORIZATION = "false"
OPS_MAY_WRITE_SIDE_STATE = "false"

SCENARIO_SCOPE_EVENT_INJECTION_STATUS = "TEST_ONLY_GUARDED"
SCENARIO_SCOPE_EVENT_PROVENANCE_TEST_INJECTION = "TEST_INJECTION"
SCENARIO_SCOPE_EVENT_PROVENANCE_UNMARKED = "UNMARKED"
REASON_SCENARIO_SCOPE_EVENT_INJECTION_REQUIRES_TEST_HARNESS = (
    "scenario_scope_event_injection_requires_explicit_test_harness_flag"
)

BACKTEST_POSITION_FEEDBACK_ROLE = "OBSERVATION_ONLY"
BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE = "false"
BACKTEST_POSITION_FEEDBACK_MAY_WRITE_RUNTIME_SCOPE_STATE = "false"

CHOP_BINDING_STATUS = "BOUND_AS_SCOPE_POLICY"
UNKNOWN_BINDING_STATUS = "NOT_BOUND_FAIL_CLOSED"
CHOP_CAN_CREATE_DIRECTION = "false"
UNKNOWN_CAN_CREATE_DIRECTION = "false"
CHOP_CAN_TRIGGER_SWITCH = "false"
UNKNOWN_CAN_TRIGGER_SWITCH = "false"
CHOP_CAN_MUTATE_SIDE_STATE = "false"
CHOP_CAN_BYPASS_TRANSITION_STATE = "false"
COMPOSITION_CHOP_STATUS = "CONSUMER_PROJECTION_ONLY"
CHOP_SEMANTIC_SSOT_COUNT = "1"

LIVE_AUTHORIZED = "false"
ORDERS_ENABLED = "false"
RUNTIME_BRIDGE_STATUS = "BOUND_NOT_ACTIVATED"

OPS_SPECIALISTS_AUTHORITY_CLASS = "NON_AUTHORITATIVE"
SCENARIO_REPLAY_AUTHORITY_CLASS = "SUBORDINATE"

REASON_OPS_SWITCH_AUTHORITY_DISABLED = "ops_switch_authority_fail_closed_disabled"
REASON_OPS_PROJECTION_ONLY = "ops_double_play_projection_diagnostic_only"
REASON_SUBORDINATE_EVALUATOR_AUTHORITY_ESCALATION = "subordinate_evaluator_authority_escalation"
REASON_COMPETING_SIDE_STATE_WRITER = "competing_side_state_writer"


class CompetingAuthorityEscalationError(RuntimeError):
    """Raised when a subordinate/non-authoritative path claims compute ownership."""


class CompetingSideStateWriterError(RuntimeError):
    """Raised when a non-canonical path claims SideState write authority."""


def assert_path_cannot_escalate_to_compute_owner_v1(
    *,
    path_id: str,
    claimed_role: str = "",
    claimed_compute_owner: str = "",
) -> None:
    """Fail-closed: Ops/scenario paths cannot become the Integrated Replay compute owner."""
    subordinate_paths = {
        "src.ops.double_play.specialists.evaluate_double_play",
        "trading.master_v2.offline_double_play_scenario_replay_v0."
        "run_offline_double_play_scenario_replay_v0",
        OPS_EVALUATE_DOUBLE_PLAY_ROLE,
        OPS_SPECIALISTS_AUTHORITY_CLASS,
        SCENARIO_REPLAY_AUTHORITY_CLASS,
    }
    claimed = str(claimed_role or "").strip()
    owner = str(claimed_compute_owner or "").strip()
    if claimed in {"COMPUTE_OWNER", "CANONICAL_COMPUTE_OWNER", CANONICAL_OFFLINE_ORCHESTRATOR}:
        raise CompetingAuthorityEscalationError(REASON_SUBORDINATE_EVALUATOR_AUTHORITY_ESCALATION)
    if owner == CANONICAL_OFFLINE_ORCHESTRATOR and str(path_id) in subordinate_paths:
        raise CompetingAuthorityEscalationError(REASON_SUBORDINATE_EVALUATOR_AUTHORITY_ESCALATION)
    if str(path_id) in subordinate_paths and claimed == CANONICAL_OFFLINE_ORCHESTRATOR:
        raise CompetingAuthorityEscalationError(REASON_SUBORDINATE_EVALUATOR_AUTHORITY_ESCALATION)


def assert_path_cannot_write_side_state_v1(
    *,
    path_id: str,
    claimed_may_write_side_state: object,
) -> None:
    """Fail-closed: only double_play_state.transition_state writes SideState/Switch."""
    truthy = claimed_may_write_side_state in (True, "true", "TRUE", "True", 1)
    if truthy:
        raise CompetingSideStateWriterError(f"{REASON_COMPETING_SIDE_STATE_WRITER}:{path_id}")


def build_double_play_sole_authority_status_fields_v1() -> Mapping[str, str]:
    return {
        "PACKAGE_MARKER": PACKAGE_MARKER,
        "CANONICAL_BULL_BEAR_STATE_OWNER": CANONICAL_BULL_BEAR_STATE_OWNER,
        "CANONICAL_SWITCH_AUTHORITY": CANONICAL_SWITCH_AUTHORITY,
        "CANONICAL_SCOPE_STATE_OWNER": CANONICAL_SCOPE_STATE_OWNER,
        "CANONICAL_SCOPE_IDENTITY_OWNER": CANONICAL_SCOPE_IDENTITY_OWNER,
        "CANONICAL_OFFLINE_ORCHESTRATOR": CANONICAL_OFFLINE_ORCHESTRATOR,
        "CANONICAL_COMPOSITION_AUTHORITY": CANONICAL_COMPOSITION_AUTHORITY,
        "OPS_EVALUATE_DOUBLE_PLAY_ROLE": OPS_EVALUATE_DOUBLE_PLAY_ROLE,
        "OPS_SWITCH_GATE_AUTHORITY_STATUS": OPS_SWITCH_GATE_AUTHORITY_STATUS,
        "OPS_SWITCH_AUTHORIZATION": OPS_SWITCH_AUTHORIZATION,
        "OPS_MAY_WRITE_SIDE_STATE": OPS_MAY_WRITE_SIDE_STATE,
        "SCENARIO_SCOPE_EVENT_INJECTION_STATUS": SCENARIO_SCOPE_EVENT_INJECTION_STATUS,
        "BACKTEST_POSITION_FEEDBACK_ROLE": BACKTEST_POSITION_FEEDBACK_ROLE,
        "BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE": (
            BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE
        ),
        "CHOP_BINDING_STATUS": CHOP_BINDING_STATUS,
        "UNKNOWN_BINDING_STATUS": UNKNOWN_BINDING_STATUS,
        "CHOP_CAN_CREATE_DIRECTION": CHOP_CAN_CREATE_DIRECTION,
        "UNKNOWN_CAN_CREATE_DIRECTION": UNKNOWN_CAN_CREATE_DIRECTION,
        "CHOP_CAN_TRIGGER_SWITCH": CHOP_CAN_TRIGGER_SWITCH,
        "UNKNOWN_CAN_TRIGGER_SWITCH": UNKNOWN_CAN_TRIGGER_SWITCH,
        "CHOP_CAN_MUTATE_SIDE_STATE": CHOP_CAN_MUTATE_SIDE_STATE,
        "CHOP_CAN_BYPASS_TRANSITION_STATE": CHOP_CAN_BYPASS_TRANSITION_STATE,
        "COMPOSITION_CHOP_STATUS": COMPOSITION_CHOP_STATUS,
        "CHOP_SEMANTIC_SSOT_COUNT": CHOP_SEMANTIC_SSOT_COUNT,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "ORDERS_ENABLED": ORDERS_ENABLED,
        "RUNTIME_BRIDGE_STATUS": RUNTIME_BRIDGE_STATUS,
        "OPS_SPECIALISTS_AUTHORITY_CLASS": OPS_SPECIALISTS_AUTHORITY_CLASS,
        "SCENARIO_REPLAY_AUTHORITY_CLASS": SCENARIO_REPLAY_AUTHORITY_CLASS,
        "DOUBLE_PLAY_PRIMARY_SSOT_CONFIRMED": "true",
    }
