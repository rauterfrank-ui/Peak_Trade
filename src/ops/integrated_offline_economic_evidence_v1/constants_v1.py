"""Constants for integrated offline economic evidence contract v1 (Increment A).

Contract/verifier/discovery only. authority_effect=NONE.
"""

from __future__ import annotations

AUTHORITY_EFFECT_NONE = "NONE"
CAPABILITY_ID = "INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1"
PACKAGE_MARKER = "INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1=true"
PRODUCER_FAMILY = "ops.integrated_offline_economic_evidence_v1"

INTEGRATED_SCHEMA_ID = "ops.integrated_offline_economic_evidence.v1"
INTEGRATED_SCHEMA_VERSION = "v1"
INTEGRATED_SCHEMA_VERSION_V1_1 = "v1.1"
SUPPORTED_INTEGRATED_SCHEMA_VERSIONS: tuple[str, ...] = ("v1", "v1.1")
INTEGRATED_ARTIFACT = "INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1.json"
INTEGRATED_VERIFIER_ID = "ops.integrated_offline_economic_evidence_verifier.v1"
CANONICAL_IDENTITY_VERIFIER_ID = "ops.integrated_offline_economic_canonical_identity_verifier.v1"

EVIDENCE_SCOPE_CONTRACT_TEST_MECHANICS = "CONTRACT_TEST_MECHANICS"
EVIDENCE_SCOPE_PRODUCTIVE_CURRENT = "PRODUCTIVE_CURRENT"

ECONOMIC_EVIDENCE_SCOPE_RATIFIED = "PER_INSTRUMENT_CURRENT_SELECTED"

INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1"
)
INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION = "v1"
PRODUCTIVE_MASTER_V2_RUNTIME_CYCLE_CAPABILITY_ID = (
    "ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1"
)
DOUBLE_PLAY_STRATEGY_INTENT_OWNER = "trading.master_v2.double_play_entry_exit_policy_v0"

EXECUTION_MODEL_SIMULATED_ECONOMICS_BRIDGE = "SIMULATED_ECONOMICS_BRIDGE"
EXECUTION_MODEL_MV2_BACKTEST_ENGINE = "MV2_BACKTEST_ENGINE"
EXECUTION_MODEL_ANALYTICAL_OBSERVATION_ONLY = "ANALYTICAL_OBSERVATION_ONLY"
SIMULATED_ECONOMICS_BRIDGE_OWNER = (
    "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
)

CRS_BINDING_PRODUCTIVE_BOUNDARY = "PRODUCTIVE_BOUNDARY_STATE_FILE"
CRS_BINDING_OFFLINE_ALGEBRA = "OFFLINE_ALGEBRA"
CRS_BINDING_RESEARCH_FIXTURE = "RESEARCH_FIXTURE"

RESIDENCY_APPLICABILITY_NOT_ENABLED = "NOT_ENABLED_FOR_EVIDENCE_SCOPE"

MD_BRIDGE_CONTRACT_ID = "CURRENT_OFFLINE_MD_BRIDGE_V1"
DECISION_EQUIVALENCE_CLASS_PRODUCTIVE = "PRODUCTIVE_CURRENT"
DECISION_EQUIVALENCE_CLASS_FIXTURE = "FIXTURE_MECHANICS_ONLY"

FORBIDDEN_STEP29M_STRATEGY_ONLY_MARKERS: tuple[str, ...] = (
    "backtest.economic_viability_evidence_v1",
    "mv2_offline_research",
    "research_fleet",
    "versioned_final_fleet",
)

ECONOMIC_METRICS_DOMAIN_SCHEMA_ID = "ops.integrated_offline_economic_metrics_domain.v1"
WALK_FORWARD_DOMAIN_SCHEMA_ID = "ops.integrated_offline_economic_walk_forward_domain.v1"
MONTE_CARLO_DOMAIN_SCHEMA_ID = "ops.integrated_offline_economic_monte_carlo_domain.v1"
STRESS_DOMAIN_SCHEMA_ID = "ops.integrated_offline_economic_stress_domain.v1"
DOMAIN_SCHEMA_VERSION = "v1"

ECONOMIC_METRICS_VERIFIER_ID = "ops.integrated_offline_economic_metrics_domain_verifier.v1"
WALK_FORWARD_VERIFIER_ID = "ops.integrated_offline_economic_walk_forward_domain_verifier.v1"
MONTE_CARLO_VERIFIER_ID = "ops.integrated_offline_economic_monte_carlo_domain_verifier.v1"
STRESS_VERIFIER_ID = "ops.integrated_offline_economic_stress_domain_verifier.v1"

CONFIG_RELPATH = "config/ops/integrated_offline_economic_evidence_v1.toml"
CONTRACT_DOC_RELPATH = "docs/ops/runbooks/INTEGRATED_OFFLINE_ECONOMIC_EVIDENCE_V1.md"

# Synthetic contract-test fixtures only; not productive discovery targets.
SYNTHETIC_FIXTURE_RELPATH_PREFIX = (
    "tests/fixtures/ops/integrated_offline_economic_evidence_contract_v1/"
)

FORBIDDEN_SUBSTITUTION_RELPATH_MARKERS: tuple[str, ...] = (
    "evidence/ops/current_6h_paper_shadow_soak_v1/",
    "integrated_paper_shadow_economic_bundle_head_bound_v1/",
    "peak_trade_robustness",
    "economic_viability_evidence_v1",
    "peak_trade_b10",
    "robustness_and_stress_v1",
)

FORBIDDEN_SUBSTITUTION_PRODUCER_MARKERS: tuple[str, ...] = (
    "backtest.economic_viability_evidence_v1",
    "peak_trade_robustness_and_stress_v1",
    "productive_wallclock",
    "integrated_paper_shadow_economic_evidence_bundle",
    "manual",
    "operator_asserted",
)

FORBIDDEN_EVIDENCE_CLASS_MARKERS: tuple[str, ...] = (
    "B10_RANKING_ROBUSTNESS_ONLY",
    "STEP29M_STATUS_ONLY",
    "WALLCLOCK_ANALYTICAL_OBSERVATION_ONLY",
    "V1_1_BUNDLE_ONLY",
    "MANUAL_AGGREGATE_BOOLEAN",
    "OFFLINE_COMPLETE_MANUAL",
)

ALLOWED_CONTRACT_TEST_PRODUCER_PREFIX = "ops.integrated_offline_economic_evidence_v1.contract_test."
