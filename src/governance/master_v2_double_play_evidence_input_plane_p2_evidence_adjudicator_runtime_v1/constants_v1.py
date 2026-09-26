"""P2 Component A — bounded evidence adjudicator runtime constants (isolated; no productive binding)."""

from __future__ import annotations

from typing import Final

PACKAGE_MARKER: Final[str] = (
    "MASTER_V2_DOUBLE_PLAY_EVIDENCE_INPUT_PLANE_P2_EVIDENCE_ADJUDICATOR_RUNTIME_V1=true"
)
WORKPACKAGE_ID: Final[str] = "P2_MASTER_V2_EVIDENCE_ADJUDICATOR_RUNTIME_V1"
OWNER: Final[str] = (
    "governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/EVIDENCE_INPUT_PLANE_P2_EVIDENCE_ADJUDICATOR_RUNTIME_V1.md"
)
OWNER_DECISION_CONFIG: Final[str] = (
    "config/governance/master_v2_double_play_evidence_input_plane_p2_owner_decision_v1.json"
)
PRODUCER_REGISTRY_CONFIG: Final[str] = (
    "config/governance/master_v2_double_play_evidence_input_plane_p2_producer_registry_v1.json"
)
BASELINE_SHA: Final[str] = "ae9da6bcb96ae2332e3399585a8eb6337f315a8a"

A_AUTHORITY: Final[str] = "BOUNDED_EVIDENCE_ADJUDICATION_ONLY"
A_TRADING_AUTHORITY: Final[str] = "NONE"
A_DP_STATE_MUTATION_AUTHORITY: Final[str] = "NONE"
A_INPUT_BINDING_AUTHORITY: Final[str] = "NONE"

IMPLEMENTS_COMPONENT_A_RUNTIME: Final[bool] = True
A_RUNTIME_IMPLEMENTED: Final[bool] = True
# Productive / downstream gate: unchanged until explicit Owner transition (P2 scope).
A_RUNTIME_IMPLEMENTATION_AUTHORIZED: Final[bool] = False
A_RUNTIME_REACHABLE: Final[bool] = False

B_RUNTIME_IMPLEMENTED: Final[bool] = False
PRODUCTIVE_ACTIVATION_AUTHORIZED: Final[bool] = False
PRODUCTIVE_L6_BINDING_AUTHORIZED: Final[bool] = False

RUNTIME_AUTHORIZATION_EFFECT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False

P1_CONTRACT_PACKAGE_MARKER: Final[str] = (
    "master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1"
)
P2_PACKAGE_PATH_MARKER: Final[str] = (
    "master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1"
)

ADMIT_DISPOSITION: Final[str] = "ADMIT"
REJECT_DISPOSITION: Final[str] = "REJECT"
STALE_DISPOSITION: Final[str] = "STALE"
CONFLICT_DISPOSITION: Final[str] = "CONFLICT"

assert A_TRADING_AUTHORITY == "NONE"
assert A_DP_STATE_MUTATION_AUTHORITY == "NONE"
assert A_INPUT_BINDING_AUTHORITY == "NONE"
assert IMPLEMENTS_COMPONENT_A_RUNTIME is True
assert A_RUNTIME_IMPLEMENTATION_AUTHORIZED is False
assert A_RUNTIME_REACHABLE is False
assert B_RUNTIME_IMPLEMENTED is False
assert PRODUCTIVE_ACTIVATION_AUTHORIZED is False
