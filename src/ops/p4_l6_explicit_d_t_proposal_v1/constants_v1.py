"""Constants for CAPABILITY_P4_L6_EXPLICIT_D_T_PROPOSAL_V1 (charter / contract only)."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_P4_L6_EXPLICIT_D_T_PROPOSAL_V1"
SCHEMA_VERSION = "explicit_dt_proposal.v1"
PROPOSAL_CONTRACT_VERSION = "p4_l6_explicit_dt_proposal.v1"
PACKAGE_MARKER = "P4_L6_EXPLICIT_D_T_PROPOSAL_V1=true"
OWNER = "ops.p4_l6_explicit_d_t_proposal_v1"
AUTHORITY_OWNER = OWNER

AUTHORITY = "PROPOSAL_CONTRACT_ONLY"
NUMERIC_FORMULA_AUTHORITY = "NONE"
PRODUCTIVE_BINDING_AUTHORIZED = False
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
RUNTIME_ACTIVATION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_AUTHORIZED = False
EXTERNAL_EFFECT_AUTHORIZED = False

NO_DEFAULT = True
NO_FORMULA = True
NO_FALLBACK = True

SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})

# Static guard: this package must never import legacy/research D_t producers.
FORBIDDEN_RUNTIME_PRODUCER_IMPORTS = frozenset(
    {
        "derive_scope_event_distances_v1",
        "compute_research_d_t_v1",
        "integrated_offline_trading_logic_replay_v1",
        "dynamic_scope_persistence_binding_v1",
        "decision_config_ownership_and_consumer_closure_v1.canonical_values_v1",
    }
)
