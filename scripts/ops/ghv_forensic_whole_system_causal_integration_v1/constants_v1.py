"""Constants for WP2-A offline causal integration."""

from __future__ import annotations

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    CAUSAL_EDGE_TYPES,
    COMPOSED_GRAPH_SCHEMA,
    MANIFEST_SCHEMA,
    STRUCTURAL_EDGE_TYPES,
)

INTEGRATION_OWNER = "scripts.ops.ghv_forensic_whole_system_causal_integration_v1"
INTEGRATION_AUTHORITY = "NONE"

CAUSAL_OVERLAY_SCHEMA = "causal_overlay.v1"
INTEGRATED_GRAPH_SCHEMA = "integrated_causal_graph.v1"
COVERAGE_GAPS_SCHEMA = "causal_coverage_gaps.v1"
INTEGRATION_MANIFEST_SCHEMA = "causal_integration_manifest.v1"
STAGE_MAPPING_SCHEMA = "stage_to_cfi_mapping.v1"

WP1_ARTIFACT_NAMES = (
    "composed_forensic_graph.v1.json",
    "crosswalk_manifest.v1.json",
    "coverage_report.v1.json",
    "ambiguity_report.v1.json",
    "excluded_non_current_report.v1.json",
)

ALLOWED_CURRENT_RELEVANCE = frozenset({"CURRENT_VERIFIED", "CURRENT_CONDITIONAL"})
FORBIDDEN_CURRENT_RELEVANCE = frozenset(
    {"NON_CURRENT", "UNKNOWN", "HISTORICAL", "RETIRED", "ARCHIVED", "OBSOLETE"}
)

ALL_TYPED_EDGE_TYPES = CAUSAL_EDGE_TYPES | STRUCTURAL_EDGE_TYPES

PROOF_CLASS_CONTRACT = "CONTRACT_CONFIRMED"
PROOF_CLASS_RUNTIME = "RUNTIME_OBSERVED"

FAILURE_INPUT_VALIDATION = "INPUT_VALIDATION_FAILURE"
FAILURE_SNAPSHOT_BINDING = "SNAPSHOT_BINDING_FAILURE"
FAILURE_IDENTITY_BINDING = "IDENTITY_BINDING_FAILURE"
FAILURE_CURRENT_RELEVANCE = "CURRENT_RELEVANCE_FAILURE"
FAILURE_RUNTIME_EVIDENCE = "RUNTIME_EVIDENCE_BINDING_FAILURE"
FAILURE_CAUSAL_EDGE = "CAUSAL_EDGE_NOT_PROVEN"
FAILURE_TEMPORAL = "TEMPORAL_CAUSALITY_NOT_PROVEN"
FAILURE_AUTHORITY_BOUNDARY = "AUTHORITY_BOUNDARY_VIOLATION"
FAILURE_OUTPUT_WRITE = "OUTPUT_WRITE_FAILURE"

CAPTURE_MANIFEST = "ghv_pre_external_runtime_capture_manifest_v1.json"
FLIGHT_RECORD = "ghv_pre_external_runtime_flight_record_v1.jsonl"
