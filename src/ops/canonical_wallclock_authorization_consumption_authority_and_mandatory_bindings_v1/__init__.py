"""CANONICAL_WALLCLOCK_AUTHORIZATION_CONSUMPTION_AUTHORITY_AND_MANDATORY_BINDINGS_V1."""

from __future__ import annotations

from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZATION_ARTIFACT_V1_CLASSIFICATION,
    AUTHORIZATION_SCHEMA_REJECTED_LEGACY,
    AUTHORIZED_VENUE,
    CANONICAL_AUTHORIZATION_SCHEMA,
    CAPABILITY_ID,
    COMPLETION_CAPABILITY_ID,
    MANDATORY_SAFETY_BOUNDARIES,
    PACKAGE_MARKER,
)

__all__ = [
    "AUTHORIZATION_ARTIFACT_V1_CLASSIFICATION",
    "AUTHORIZATION_SCHEMA_REJECTED_LEGACY",
    "AUTHORIZED_VENUE",
    "CANONICAL_AUTHORIZATION_SCHEMA",
    "CAPABILITY_ID",
    "COMPLETION_CAPABILITY_ID",
    "MANDATORY_SAFETY_BOUNDARIES",
    "PACKAGE_MARKER",
    "compute_effective_session_config_digest_v1",
    "consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1",
    "verify_productive_authorization_authority_inventory_v1",
    "verify_wallclock_v2_gate_call_graph_v1",
]


def __getattr__(name: str):
    if name == "compute_effective_session_config_digest_v1":
        from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.effective_session_config_digest_v1 import (
            compute_effective_session_config_digest_v1,
        )

        return compute_effective_session_config_digest_v1
    if name == "consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1":
        from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.wallclock_v2_gatekeeper_v1 import (
            consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1,
        )

        return consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1
    if name == "verify_wallclock_v2_gate_call_graph_v1":
        from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.call_graph_contract_v1 import (
            verify_wallclock_v2_gate_call_graph_v1,
        )

        return verify_wallclock_v2_gate_call_graph_v1
    if name == "verify_productive_authorization_authority_inventory_v1":
        from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.authority_inventory_v1 import (
            verify_productive_authorization_authority_inventory_v1,
        )

        return verify_productive_authorization_authority_inventory_v1
    raise AttributeError(name)
