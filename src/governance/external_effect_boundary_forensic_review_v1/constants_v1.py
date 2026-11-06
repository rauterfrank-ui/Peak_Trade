"""Forensic census for EXTERNAL_EFFECT boundary review v1 (proof-only)."""

from __future__ import annotations

PACKAGE_MARKER = "EXTERNAL_EFFECT_BOUNDARY_FORENSIC_REVIEW_V1=true"
OWNER = "governance.external_effect_boundary_forensic_review_v1"
CONTRACT_VERSION = "external_effect_boundary_forensic_review.v1"
BASELINE_ORIGIN_MAIN_SHA = "7330b6cb8a3cfccca9163028cbdf13e13910088c"

WORKPACKAGE_ID = "EXTERNAL_EFFECT_BOUNDARY_FORENSIC_REVIEW_V1"
NORMATIVE_SPEC = "docs/ops/specs/EXTERNAL_EFFECT_BOUNDARY_FORENSIC_REVIEW_V1.md"
DECISION_CONFIG = "config/governance/external_effect_boundary_forensic_review_v1_decision_v1.json"
OWNER_WP_DECISION_CONFIG = (
    "config/governance/external_effect_boundary_forensic_review_wp_v1_owner_decision_v1.json"
)

MASTER_RUNBOOK_PRODUCTIVE_BOUNDARY_SECTION = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"

PRE_EXTERNAL_BOUNDARY_OWNER = "ops.pre_external_to_external_effect_boundary_bounded_wp_v1"
EXECUTION_BOUNDARY_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1.execution_boundary_v1."
    "halt_at_live_execution_boundary_v1"
)
EXTERNAL_EFFECT_GATE_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1."
    "evaluate_external_effect_v1"
)
ENVELOPE_SEND_SEAM_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1."
    "envelope_bound_external_effect_send_seam_v1."
    "attempt_envelope_bound_external_effect_send_v1"
)
EXTERNAL_EFFECT_PERMIT_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1"
)
CREDENTIAL_BOUNDARY_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1."
    "checkout_independent_credential_source_backend_kind_v1"
)
VENUE_POST_SINK_OWNER = (
    "src.ops.full_core_live_path_composition_root_v1."
    "full_core_productive_http_post_transport_v1.FullCoreProductiveHttpTradeOrderTransportV1."
    "post_trade_order"
)

BOUNDARY_CHAIN_SURFACES = (
    "src/ops/full_core_live_path_composition_root_v1/execution_boundary_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/external_effect_gate_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py",
)

GOVERNED_UPSTREAM_POLICY_SURFACES = (
    "src/governance/current_productive_activation_policy_v1.py",
    "src/governance/current_continuous_run_policy_v1.py",
    "src/governance/current_continuous_run_runtime_binding_v1.py",
)

EXTERNAL_EFFECT_BOUNDARY_REVIEW_COMPLETE = True
REQUIRED_CLOSURE_COUNT = 0
UNKNOWN_BOUNDARY_PATH_COUNT = 0

CONTINUOUS_RUN_ADJUDICATION_CLASS = "POLICY_AUTHORIZED_ORCHESTRATOR_MODULE_PIN_FALSE"
EXTERNAL_EFFECT_ADJUDICATION_CLASS = "STANDING_FALSE_FAIL_CLOSED"
PRE_EXTERNAL_ADJUDICATION_CLASS = "PROVEN_STATIC_CENSUS"
PERMIT_ADJUDICATION_CLASS = "INTENTIONALLY_ISOLATED_OWNER_GO"
CREDENTIAL_ADJUDICATION_CLASS = "CAPABILITY_WITHOUT_ACCESS_AUTHORIZATION"
POST_SINK_ADJUDICATION_CLASS = "IDENTIFIED_NOT_REACHABLE_WITH_CURRENT_AUTHORITY"

assert EXTERNAL_EFFECT_BOUNDARY_REVIEW_COMPLETE is True
assert REQUIRED_CLOSURE_COUNT == 0
assert UNKNOWN_BOUNDARY_PATH_COUNT == 0

__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "BOUNDARY_CHAIN_SURFACES",
    "CONTRACT_VERSION",
    "CONTINUOUS_RUN_ADJUDICATION_CLASS",
    "CREDENTIAL_ADJUDICATION_CLASS",
    "CREDENTIAL_BOUNDARY_OWNER",
    "DECISION_CONFIG",
    "ENVELOPE_SEND_SEAM_OWNER",
    "EXECUTION_BOUNDARY_OWNER",
    "EXTERNAL_EFFECT_ADJUDICATION_CLASS",
    "EXTERNAL_EFFECT_BOUNDARY_REVIEW_COMPLETE",
    "EXTERNAL_EFFECT_GATE_OWNER",
    "EXTERNAL_EFFECT_PERMIT_OWNER",
    "GOVERNED_UPSTREAM_POLICY_SURFACES",
    "MASTER_RUNBOOK_PRODUCTIVE_BOUNDARY_SECTION",
    "NORMATIVE_SPEC",
    "OWNER",
    "OWNER_WP_DECISION_CONFIG",
    "PACKAGE_MARKER",
    "PERMIT_ADJUDICATION_CLASS",
    "POST_SINK_ADJUDICATION_CLASS",
    "PRE_EXTERNAL_ADJUDICATION_CLASS",
    "PRE_EXTERNAL_BOUNDARY_OWNER",
    "REQUIRED_CLOSURE_COUNT",
    "UNKNOWN_BOUNDARY_PATH_COUNT",
    "VENUE_POST_SINK_OWNER",
    "WORKPACKAGE_ID",
]
