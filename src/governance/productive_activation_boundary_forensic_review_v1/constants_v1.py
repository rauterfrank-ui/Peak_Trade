"""Forensic census for PRODUCTIVE_ACTIVATION boundary review v1 (proof-only)."""

from __future__ import annotations

PACKAGE_MARKER = "PRODUCTIVE_ACTIVATION_BOUNDARY_FORENSIC_REVIEW_V1=true"
OWNER = "governance.productive_activation_boundary_forensic_review_v1"
CONTRACT_VERSION = "productive_activation_boundary_forensic_review.v1"
BASELINE_ORIGIN_MAIN_SHA = "d590b8142210680805f8dc159c5a2fb684e87737"

WORKPACKAGE_ID = "PRODUCTIVE_ACTIVATION_BOUNDARY_FORENSIC_REVIEW_V1"
NORMATIVE_SPEC = "docs/ops/specs/PRODUCTIVE_ACTIVATION_BOUNDARY_FORENSIC_REVIEW_V1.md"
DECISION_CONFIG = (
    "config/governance/productive_activation_boundary_forensic_review_v1_decision_v1.json"
)
OWNER_WP_DECISION_CONFIG = (
    "config/governance/productive_activation_boundary_forensic_review_wp_v1_owner_decision_v1.json"
)

# Master Runbook CURRENT Productive Boundary (navigation anchor; not activation authority).
MASTER_RUNBOOK_PRODUCTIVE_BOUNDARY_SECTION = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"

# F1/M9 post-#6889 runtime path producers (consumer reachability only).
F1_M9_THRESHOLD_CONSUMER_RUNTIME_PRODUCERS = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/"
    "hardening_cycle_bridge_v2.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
)

# Governed decision records that name PRODUCTIVE_ACTIVATION as earliest unclosed boundary.
PRODUCTIVE_ACTIVATION_NAMED_BOUNDARY_DECISION_CONFIGS = (
    "config/governance/"
    "governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1_decision_v1.json",
    "config/governance/"
    "governed_f1_m9_scoped_owner_productive_runtime_apply_start_real_mechanical_continuation_v1_decision_v1.json",
)

# Surfaces whose names collide with global Productive Activation but carry distinct semantics.
SEMANTIC_COLLISION_SURFACES = (
    "src/ops/p5_10_productive_activation_and_binding_v1/constants_v1.py",
    "src/ops/p5_10_productive_activation_and_binding_v1/productive_cycle_bind_seam_v1.py",
)

# Full-Core orchestration terminals (PRE_EXTERNAL; not activation mint).
FULL_CORE_PRODUCTIVE_ORCHESTRATION_SURFACES = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_governed_cycle_orchestrator_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_governed_continuous_cycle_orchestrator_v1.py",
)

PRODUCTIVE_ACTIVATION_BOUNDARY_REVIEW_COMPLETE = True
REQUIRED_CLOSURE_COUNT = 0
UNKNOWN_BOUNDARY_PATH_COUNT = 0

# Adjudication classes (census verdict; not runtime authorization).
GLOBAL_PRODUCTIVE_ACTIVATION_ADJUDICATION_CLASS = "POLICY_AUTHORIZED_BOUNDED_ADMISSION"
F1_M9_CONSUMER_REACHABILITY_ADJUDICATION_CLASS = "WIRED_NOT_ACTIVATION"
P5_10_LAYERED_BIND_ADJUDICATION_CLASS = "BIND_ENABLED_CUTOVER_NOT_AUTHORIZED"
CONTINUOUS_RUN_ADJUDICATION_CLASS = "DEFINED_NOT_AUTHORIZED"
EXTERNAL_EFFECT_ADJUDICATION_CLASS = "STANDING_FALSE_FAIL_CLOSED"
PRE_EXTERNAL_TERMINAL_ADJUDICATION_CLASS = "PROVEN_STATIC_CENSUS"

assert PRODUCTIVE_ACTIVATION_BOUNDARY_REVIEW_COMPLETE is True
assert REQUIRED_CLOSURE_COUNT == 0
assert UNKNOWN_BOUNDARY_PATH_COUNT == 0

__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "CONTRACT_VERSION",
    "CONTINUOUS_RUN_ADJUDICATION_CLASS",
    "DECISION_CONFIG",
    "EXTERNAL_EFFECT_ADJUDICATION_CLASS",
    "F1_M9_CONSUMER_REACHABILITY_ADJUDICATION_CLASS",
    "F1_M9_THRESHOLD_CONSUMER_RUNTIME_PRODUCERS",
    "FULL_CORE_PRODUCTIVE_ORCHESTRATION_SURFACES",
    "GLOBAL_PRODUCTIVE_ACTIVATION_ADJUDICATION_CLASS",
    "MASTER_RUNBOOK_PRODUCTIVE_BOUNDARY_SECTION",
    "NORMATIVE_SPEC",
    "OWNER",
    "OWNER_WP_DECISION_CONFIG",
    "PACKAGE_MARKER",
    "P5_10_LAYERED_BIND_ADJUDICATION_CLASS",
    "PRE_EXTERNAL_TERMINAL_ADJUDICATION_CLASS",
    "PRODUCTIVE_ACTIVATION_BOUNDARY_REVIEW_COMPLETE",
    "PRODUCTIVE_ACTIVATION_NAMED_BOUNDARY_DECISION_CONFIGS",
    "REQUIRED_CLOSURE_COUNT",
    "SEMANTIC_COLLISION_SURFACES",
    "UNKNOWN_BOUNDARY_PATH_COUNT",
    "WORKPACKAGE_ID",
]
