"""Constants for productive typed-volatility producer + CMC hot-path binding v1."""

from __future__ import annotations

CAPABILITY_ID = "PRODUCTIVE_TYPED_VOLATILITY_PRODUCER_AND_CMC_HOT_PATH_BINDING_V1"
PACKAGE_MARKER = "PRODUCTIVE_TYPED_VOLATILITY_PRODUCER_AND_CMC_HOT_PATH_BINDING_V1=true"
OWNER = "ops.productive_typed_volatility_producer_and_cmc_hot_path_binding_v1"
SCHEMA_VERSION = "v1"

CORE_LOGIC_CHANGE = False
NO_NEW_VOLATILITY_FORMULA = True
NO_NUMERIC_THRESHOLD_CHANGE = True
NO_WINDOW_CHANGE = True
NO_DDOF_CHANGE = True
NO_UNIT_CHANGE = True
NO_ANNUALIZATION_CHANGE = True
NO_TIMEFRAME_CHANGE = True
NO_PROXY_PROMOTION = True
NO_LEGACY_FLOAT_AUTHORITY = True
NO_SILENT_DEFAULT = True
NO_SYNTHETIC_VOLATILITY = True
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False
NUMERIC_MAX_AGE_EFFECT = "DIAGNOSTIC_ONLY"

TYPED_VOLATILITY_PRODUCER = (
    "trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1"
)
PRODUCTIVE_PRODUCER_CALLER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    ".wallclock_hardening_binding_v2.run_hardened_wallclock_bridge_observation_cycle_v2"
)
VOLATILITY_STATE_OWNER = "trading.master_v2.canonical_volatility_runtime_mark_history_v1"
CMC_BINDING_CALLER = (
    "trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1"
)
PRESENCE_GATE_CONSUMER = "trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1"
PT1M_FINALIZER_OWNER = "trading.master_v2.canonical_volatility_pt1m_mark_observation_finalizer_v1"

WARMUP_REQUIRED_PRICE_OBSERVATIONS = 61
PERSISTENCE_CLASSIFICATION = "PERSIST_DIRECTLY_WHEN_PATH_CONFIGURED_ELSE_PROCESS_LOCAL_CONTINUITY"
RESTART_SEMANTICS = (
    "History restores via existing mark-history persistence when configured; "
    "estimate remains fail-closed until next PRODUCED. "
    "Wallclock sessions without persistence_path keep process-local continuity only; "
    "cross-process restart without persistence remains an explicit open boundary."
)

ROOT_CAUSE_CALL_GRAPH_EDGE = (
    "run_hardened_wallclock_bridge_observation_cycle_v2"
    "->run_hardened_bridge_cycle_v2(missing finalized_pt1m_*)"
    "->apply_to_market_context_v1(ingest_sample=False)"
    "->on_runtime_cycle_without_sample_v1"
    "->producer_outcome=WARMUP permanent"
)
