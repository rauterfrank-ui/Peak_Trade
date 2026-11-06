"""Constants for the read-only Master V2 outer-boundary projector."""

from __future__ import annotations

PROJECTOR_ID = "MV2_OUTER_BOUNDARY_PROJECTOR_V1"
RESOLVER_ID = "MV2_SYMBOL_ENDPOINT_RESOLVER_V1"
TARGET_IDENTITY = "MASTER_V2"
SCOPE = "OUTER_MEMBERSHIP_AND_DIRECT_BOUNDARY_EDGES"
MAX_OUTER_DEPTH = 1

AUTHORITY = "NONE"
TRADING_AUTHORITY = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
GRAPH_PROJECTION_AUTHORITY = "NONE"

ALLOWED_BOUNDARY_STATUSES = frozenset({"PARTIAL", "NOT_PROVEN", "BLOCKED_BY_EVIDENCE"})
FORBIDDEN_BOUNDARY_STATUSES = frozenset(
    {
        "RATIFIED",
        "VERIFIED_UNIVERSE_OUTER_BOUNDARY",
        "CURRENT_BOUNDARY_IMPLEMENTATION_PROVEN",
    }
)

OWNER_RELATION_CLASSES = frozenset({"DATA", "DECISION", "STATE", "AUTHORITY", "SAFETY", "EVIDENCE"})
FORBIDDEN_AUTHORITY_DERIVATIONS = frozenset({"DECISION_FLOW", "HANDOFF", "AUTHORIZES"})
REJECTED_MEMBERSHIP_BASES = frozenset(
    {
        "FILENAME",
        "DIRECTORY",
        "CENSUS_TAXONOMY",
        "LANDSCAPE_LABEL",
        "GRAPH_NEIGHBORHOOD",
    }
)

DECISION_SPEC_PATH = "docs/ops/specs/MV2_DECISION_PATH_BOUNDARY_V1.md"
CENSUS_PATH = "config/governance/current_system_census_graph_v1/source_v1.json"
LANDSCAPE_PATH = "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"
REPLAY_PATH = "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
CYCLE_PATH = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_master_v2_runtime_cycle_v1.py"
)
HARDENING_PATH = "src/trading/master_v2/naked_mv2_double_play_core_authority_hardening_v1.py"
GHOSV_EXECUTION_PATH = "src/ops/ghosv_bounded_context_v1/pipeline_v1.py"

REPLAY_SYMBOL = "run_integrated_offline_trading_logic_replay_v1"
REPLAY_COMPONENT_ID = (
    "symbol:trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
CYCLE_OWNER_CITATION = (
    'CYCLE_OWNER = (\n    "trading.master_v2.integrated_offline_trading_logic_replay_v1."\n'
    '    "run_integrated_offline_trading_logic_replay_v1"\n)'
)
DOUBLE_PLAY_ROLE_CITATION = 'DOUBLE_PLAY_ROLE = "COMPOSITION_STATE_ENTRY_EXIT_WITHIN_JOINT_CORE"'

REQUIRED_DECISION_LINES = (
    "OWNER_DECISION_ID=MV2_DECISION_PATH_BOUNDARY_V1",
    "DECISION_OWNER=INTEGRATED_REPLAY",
    "MASTER_V2_INTENDED_UNIVERSE=true",
    "DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA=true",
    "DOUBLE_PLAY_SEPARATE_UNIVERSE=false",
    "FULL_UNIVERSE_BOUNDARY_RATIFIED=false",
    "CURRENT_BOUNDARY_IMPLEMENTATION_PROVEN=false",
    "AUTHORITY_TRANSFER=false",
    "GRAPH_PROJECTION_AUTHORITY=NONE",
    "CURRENT_GHOSV_AUTHORITY=NONE",
)

NON_TRANSFER_MARKERS = (
    ("selection", "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"),
    ("binding", "BoundInstrumentV1"),
    ("reconciliation", "RECONCILIATION_AUTHORITY_TRANSFER=False"),
    ("market_data_provenance", "ProductiveCycleCanonicalPriceProvenanceV1"),
    ("kill_switch_reader", "durable_kill_switch_mv2_binding_v1"),
    ("exit_policy", "ops.exit_policy_producer_binding_v1"),
    ("crs", "_wire_simulated_economics_crs_boundary_onto_replay_input_v1"),
    ("risk", "- Risk."),
    ("capital", "- Capital."),
    ("order_intent", "- Order Intent."),
    ("execution", "- Execution."),
)

GHV_CROSSWALK_DIR = "scripts/ops/ghv_forensic_whole_system_crosswalk_v1"
GHV_PURE_FILES = (
    "constants_v1.py",
    "identity_v1.py",
    "edges_v1.py",
    "traversal_v1.py",
)
CAUSAL_INTEGRATION_PATH = (
    "scripts/ops/ghv_forensic_whole_system_causal_integration_v1/integrate_v1.py"
)

MV2_PLANES = frozenset({"mv2_double_play", "td-mv2-dp"})
CENSUS_TOPOLOGY_ID = "TD-MV2-DP"

FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "trading",
        "execution",
        "risk",
        "ghosv_bounded_context_v1",
    }
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.trading",
    "src.execution",
    "src.risk",
    "src.ops.ghosv_bounded_context_v1",
    "trading.",
    "execution.",
    "risk.",
)
