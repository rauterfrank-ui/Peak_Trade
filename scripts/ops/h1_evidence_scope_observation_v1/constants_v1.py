"""H1 evidence-scope observation constants. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

SCHEMA_ID: Final = "H1_EVIDENCE_SCOPE_OBSERVATION_V1"
SCHEMA_VERSION: Final = 1
MANIFEST_ID: Final = "h1-evidence-scope-observation-v1"

AUTHORITY: Final = "NONE"
TRADING_AUTHORITY: Final = "NONE"
SAFETY_AUTHORITY: Final = "NONE"
EXECUTION_AUTHORITY: Final = "NONE"
RUNTIME_AUTHORIZATION_EFFECT: Final = "NONE"
GUARDIAN_IDENTITY: Final = False
COVERAGE_PROOF: Final = False
NETWORK_ACCESS: Final = False
REPOSITORY_EVIDENCE_WRITE: Final = False
PRIVATE_GET_EXECUTED: Final = False
POST_EXECUTED: Final = False
STATE_WRITE_EXECUTED: Final = False
CAUSAL_INTEGRATOR_INVOKED: Final = False
DOMAIN_VERIFICATION: Final = False
CURRENT_CENSUS_PROVEN: Final = False
H1_MEMBERSHIP_COMPLETE: Final = False
HISTORICAL_PINS_REWRITTEN: Final = False
GRAPH_CURRENT_FLAG_ADOPTED: Final = False

PROVEN_CURRENT: Final = "PROVEN_CURRENT"
UNASSIGNED_FINDING_STATUS: Final = "UNASSIGNED"
ABSENCE_CATEGORY: Final = "ABSENCE"
PRESENCE_CATEGORY: Final = "PRESENCE"

CENSUS_RELATIVE: Final = "config/governance/current_system_census_graph_v1/source_v1.json"
LANDSCAPE_RELATIVE: Final = (
    "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"
)
GRAPH_RELATIVES: Final = (
    "evidence/ops/wp_r2b_r4_presentation_retirement_v1/20261016T041630Z/composed_forensic_graph.v1.json",
    "evidence/ops/wp_r2b_r4_presentation_retirement_v1/20261016T043611Z_r4_final/composed_forensic_graph.v1.json",
)

H1_SCOPE_NODES: Final = (
    "H1_GET_EVIDENCE_ADMISSION",
    "H1_DECISION_PUBLICATION_CONSUMER",
)
H1_PATH_BY_NODE: Final = {
    "H1_GET_EVIDENCE_ADMISSION": "src/ops/h1_get_evidence_admission_v1",
    "H1_DECISION_PUBLICATION_CONSUMER": "src/ops/h1_decision_publication_consumer_v1",
}

TOOL_SLOTS: Final = {
    "DOMAIN_GHV": "PRESENT_UNBOUND",
    "DOMAIN_CURRENT_CAUSAL_GRAPH": "PRESENT_UNBOUND",
    "DOMAIN_GHOSV": "PRESENT_UNBOUND",
}

FORBIDDEN_OUTPUT_KEYS: Final = frozenset(
    {
        "overall_pass",
        "guardian_pass",
        "universe_pass",
        "live_authorized",
        "coverage_pass",
    }
)
FORBIDDEN_FINDING_CATEGORIES: Final = frozenset({"AUTHORITY"})
