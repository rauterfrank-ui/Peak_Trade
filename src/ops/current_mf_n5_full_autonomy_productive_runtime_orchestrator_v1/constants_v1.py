"""Constants for productive Full-Autonomy N=5 runtime orchestrator V1.

Composes existing join owners only. No trading-decision authority.
Terminal boundary: PRE_EXTERNAL_EFFECT (readiness rollup); optional
host-completion rollup is orchestration-only and stays fail-closed on
external effect.
"""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED as FULL_CORE_EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED as FULL_CORE_POST_ALLOWED,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    CANONICAL_RESTART_RECONSTRUCTABLE as PORTFOLIO_CANONICAL_RESTART_RECONSTRUCTABLE,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP23_MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CAP23_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE as CAP24_MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CAP24_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

OWNER = "ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1"
CONTRACT_ID = "CURRENT_MF_N5_FULL_AUTONOMY_PRODUCTIVE_RUNTIME_ORCHESTRATOR_CONTRACT_V1"
SCHEMA_VERSION = "current_mf_n5_full_autonomy_productive_runtime_orchestrator.v1"
SLICE_ID = "PRODUCTIVE_FULL_AUTONOMY_N5_RUNTIME_ORCHESTRATOR"
OWNER_GO_THIS_SLICE = "OWNER_GO_PR2_FULL_AUTONOMY_PRODUCTIVE_RUNTIME_ORCHESTRATOR"

ENTRYPOINT_SYMBOL = "run_productive_full_autonomy_n5_runtime_orchestrator_v1"
PRODUCTIVE_ENTRYPOINT = f"{OWNER}.{ENTRYPOINT_SYMBOL}"
HARNESS_JOIN_CHAIN_REPLACED = False

AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "PRODUCTIVE_FA_RUNTIME_ORCHESTRATION_COMPOSE_ONLY"
AUTONOMY_ORCHESTRATOR_STATUS = "PRODUCTIVE_COMPOSE_IMPLEMENTED"
AUTONOMY_TRADING_DECISION_AUTHORITY = False
FULL_AUTONOMY_TRADING_DECISION_AUTHORITY = False
JOIN_RANKING_AUTHORITY = False
JOIN_SELECTION_AUTHORITY = False
JOIN_CAP23_SELECTION_AUTHORITY = False
JOIN_CAP24_BINDING_AUTHORITY = False
JOIN_TRADING_AUTHORITY = False
JOIN_EXECUTION_AUTHORITY = False
JOIN_FULL_AUTONOMY_HOST_AUTHORITY = False
PARALLEL_AUTHORITY_CREATED = False
MF_PRODUCTIVE_JOIN = False
HOST_JOIN = False
EXECUTION_CONCURRENCY_AUTHORIZED = False
EXECUTION_SCHEDULE = "SEQUENTIAL_LANE_ID_ORDER_NOT_CONCURRENT"

MAX_POSITIONS_EFFECTIVE = int(CAP23_MAX_POSITIONS_EFFECTIVE)
MULTI_FUTURE_RUNTIME_AUTHORIZED = bool(CAP23_MULTI_FUTURE_RUNTIME_AUTHORIZED)
N_GT_1_ENABLED = False
EXTERNAL_EFFECT_AUTHORIZED = FULL_CORE_EXTERNAL_EFFECT_AUTHORIZED
POST_ALLOWED = FULL_CORE_POST_ALLOWED
ATLAS_AUTHORITY = "NONE"

TERMINAL_BOUNDARY_PRE_EXTERNAL = "PRE_EXTERNAL_EFFECT_ORCHESTRATION_ROLLUP"
TERMINAL_BOUNDARY_FAIL_CLOSED = "FAIL_CLOSED"

PORTFOLIO_RESTART_STATUS = (
    "FAIL_CLOSED_NO_UNPROVEN_RESTORE"
    if PORTFOLIO_CANONICAL_RESTART_RECONSTRUCTABLE is False
    else "UNKNOWN"
)

RECOVERED_TOPOLOGY_OWNER = "ops.current_mf_n5_recovered_topology_consumer_join_v1"
CAP23_PRODUCE_JOIN_OWNER = "ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1"
CAP24_BIND_JOIN_OWNER = "ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1"
BOUND_INGEST_OWNER = "ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1"
MV2_DP_HANDOFF_OWNER = "ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1"
GOVERNED_CYCLE_READINESS_OWNER = (
    "ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1"
)
N5_COMPLETION_OWNER = "ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1"
PORTFOLIO_BUDGET_OWNER = "portfolio_capital_reservation_budget_owner_v1"
CRS_QUANTITY_OWNER = "src.governance.capital_risk_sizing_v1"
FIRST_TRADING_DECISION_CONSUMER = "run_current_productive_master_v2_runtime_cycle_v1"

assert MAX_POSITIONS_EFFECTIVE == int(CAP24_MAX_POSITIONS_EFFECTIVE) == 1
assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
assert CAP24_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
assert N_GT_1_ENABLED is False
assert EXTERNAL_EFFECT_AUTHORIZED is False
assert POST_ALLOWED is False
assert AUTONOMY_TRADING_DECISION_AUTHORITY is False
assert MF_PRODUCTIVE_JOIN is False
assert HOST_JOIN is False
assert ATLAS_AUTHORITY == "NONE"

FAILURE_AUTHORITY = "PRODUCTIVE_FA_RUNTIME_ORCHESTRATOR_AUTHORITY_CLAIM_FORBIDDEN"
FAILURE_CARDINALITY = "PRODUCTIVE_FA_RUNTIME_ORCHESTRATOR_CARDINALITY_MISMATCH"
FAILURE_FORBIDDEN_KWARG = "PRODUCTIVE_FA_RUNTIME_ORCHESTRATOR_FORBIDDEN_KWARG"
FAILURE_EXTERNAL_EFFECT = "PRODUCTIVE_FA_RUNTIME_ORCHESTRATOR_EXTERNAL_EFFECT"
FAILURE_LANE_ISOLATION = "PRODUCTIVE_FA_RUNTIME_ORCHESTRATOR_LANE_ISOLATION"
FAILURE_TERMINAL = "PRODUCTIVE_FA_RUNTIME_ORCHESTRATOR_TERMINAL_FAIL_CLOSED"

FORBIDDEN_COMPOSE_KWARGS = frozenset(
    {
        "enable_host",
        "host_enabled",
        "host_join",
        "attempt_submit",
        "attempt_wire_send",
        "execute_network",
        "perform_get",
        "permit_mint",
        "live_port",
        "mf_productive_join",
        "multi_future_runtime_authorized",
        "execution_concurrency",
    }
)
