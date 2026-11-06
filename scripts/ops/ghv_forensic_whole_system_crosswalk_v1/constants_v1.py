"""Constants for forensic crosswalk v1."""

from __future__ import annotations

OWNER = "scripts.ops.ghv_forensic_whole_system_crosswalk_v1"
CROSSWALK_AUTHORITY = "NONE"
CFI_SCHEMA = "peak_trade.forensic_canonical_identity.v1"
COMPOSED_GRAPH_SCHEMA = "composed_forensic_graph.v1"
MANIFEST_SCHEMA = "crosswalk_manifest.v1"

CENSUS_PATH = "config/governance/current_system_census_graph_v1/source_v1.json"
LANDSCAPE_PATH = "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"
ATLAS_CENSUS_META = "docs/system_atlas/census/census_meta.yaml"
ATLAS_CATALOG = "docs/system_atlas/entities/catalog.yaml"
ATLAS_STRUCTURAL = "docs/system_atlas/relations/structural.yaml"

CURRENT_EPISTEMIC_ALLOW = frozenset({"PROVEN_CURRENT"})
CURRENT_CENSUS_STATUS_ALLOW = frozenset({"PROVEN_CURRENT"})
CURRENT_LANDSCAPE_STATUS_ALLOW = frozenset({"PROVEN_CURRENT"})
ATLAS_EPISTEMIC_EXCLUDE = frozenset({"HISTORICAL", "HYPOTHESIS", "OPEN"})
ATLAS_RELATION_EPISTEMIC_ALLOW = frozenset(
    {
        "PROVEN_CURRENT",
        "CANONICAL_AUTHORITY",
        "ADJUDICATED",
    }
)

CAUSAL_EDGE_TYPES = frozenset(
    {
        "CALLS",
        "PRODUCES",
        "CONSUMES",
        "READS_STATE",
        "WRITES_STATE",
        "PERSISTS",
        "RESTORES",
        "EMITS_EVENT",
        "HANDLES_EVENT",
        "SCHEDULES",
        "TRANSFORMS",
        "HANDOFF",
        "FEEDBACK",
        "EXTERNAL_EFFECT",
        "BLOCKS",
        "AUTHORIZES",
    }
)
STRUCTURAL_EDGE_TYPES = frozenset({"IMPORTS", "CONFIGURES", "OBSERVES"})
